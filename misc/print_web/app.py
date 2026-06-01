"""
PyPrint - LAN Print Server
Flask-based print server with Anthropic-styled UI.
"""
import os
import sys
import tempfile
import time
from datetime import datetime

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename

from utils.printers import PrinterManager
from utils.file_handler import FileHandler
from utils.auth import get_user_manager
from utils.db_activation_codes import generate_code, validate_code, use_code, list_codes, delete_code as db_delete_code
from utils.db_print_jobs import get_print_history, get_print_stats, log_print_job
from utils.db_users import list_users as db_list_users

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable must be set")
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Initialize managers
printer_manager = PrinterManager()
file_handler = FileHandler()
user_manager = get_user_manager()


@app.context_processor
def inject_now():
    """Inject current year and user info into all templates."""
    user = None
    if 'user_id' in session:
        user = user_manager.get_user(session['user_id'])
    return {
        'current_year': datetime.now().year,
        'current_user': user
    }


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


def login_required(f):
    """Decorator to require login for a route."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/') or request.is_json:
                return jsonify({'error': 'Login required', 'login_url': url_for('login')}), 401
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for a route."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        if session.get('user_role') != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def index():
    """Main page - file upload and print."""
    printers = printer_manager.get_printers()
    return render_template('index.html', printers=printers)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if username and password:
            user = user_manager.verify_user(username, password)
            if user:
                session['user_id'] = user['username']
                session['user_role'] = user.get('role', 'user')
                next_url = request.args.get('next') or url_for('index')
                return redirect(next_url)
            else:
                error = 'Invalid username or password'
        else:
            error = 'Please enter username and password'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        activation_code = request.form.get('activation_code', '').strip()

        if not username or not password or not activation_code:
            error = '请填写所有必填字段'
            return render_template('register.html', error=error)

        # Validate activation code
        code_info = validate_code(activation_code)
        if not code_info or not code_info.get('valid'):
            error = code_info.get('error', '激活码无效') if code_info else '激活码无效'
            return render_template('register.html', error=error)

        # Create user
        result = user_manager.add_user(username, password, role='user')
        if not result:
            error = '用户名已存在'
            return render_template('register.html', error=error)

        # Mark code as used
        use_code(activation_code, username)

        # Auto login
        session['user_id'] = username
        session['user_role'] = 'user'
        return redirect(url_for('index'))

    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
@admin_required
def admin_page():
    """Admin dashboard."""
    return render_template('admin.html')


@app.route('/api/printers')
@login_required
def api_printers():
    """Get available printers."""
    try:
        printers = printer_manager.get_printers()
        if printers is None:
            printers = []
        response = jsonify({
            'printers': [{'name': p['name'], 'is_default': p.get('is_default', False), 'status': p.get('status', 'ready')} for p in printers],
            'platform': sys.platform
        })
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'printers': [], 'platform': sys.platform, 'error': str(e)}), 500


@app.route('/api/print', methods=['POST'])
@login_required
def api_print():
    """Handle print job submission."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    file = request.files['file']
    printer_name = request.form.get('printer')
    copies = int(request.form.get('copies', 1))
    page_range = request.form.get('page_range', '')
    orientation = request.form.get('orientation', 'portrait')
    paper_size = request.form.get('paper_size', 'auto')
    paper_source = request.form.get('paper_source', 'auto')
    scaling = int(request.form.get('scaling', 100))
    print_quality = request.form.get('print_quality', 'auto')
    color_mode = request.form.get('color_mode', 'auto')
    duplex = request.form.get('duplex', 'none')
    collate = request.form.get('collate', '1') == '1'

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not printer_name:
        return jsonify({'success': False, 'error': 'No printer selected'}), 400

    # Validate file type
    if not file_handler.is_allowed_file(file.filename):
        return jsonify({'success': False, 'error': '不支持的文件类型'}), 400

    try:
        # Save to temp file - preserve original extension
        original_filename = file.filename
        # Get the extension from original filename
        ext = os.path.splitext(original_filename)[1].lower() if original_filename else ''
        # Create secure base name but keep extension
        safe_basename = secure_filename(os.path.splitext(original_filename)[0]) or 'file'
        filename = f"{safe_basename}_{int(time.time())}{ext}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        # Submit print job
        result = printer_manager.print_file(
            printer_name=printer_name,
            file_path=temp_path,
            copies=copies,
            page_range=page_range,
            orientation=orientation,
            paper_size=paper_size,
            paper_source=paper_source,
            scaling=scaling,
            print_quality=print_quality,
            color_mode=color_mode,
            duplex=duplex,
            collate=collate
        )

        # Cleanup temp file
        try:
            os.remove(temp_path)
        except Exception:
            pass

        if result['success']:
            log_print_job(
                job_id=result.get('job_id', f'print-{int(time.time())}'),
                user_id=session.get('user_id', 'unknown'),
                printer_name=printer_name,
                file_name=original_filename or 'unknown',
                copies=copies
            )
            return jsonify({
                'success': True,
                'message': f'打印任务已发送到 {printer_name}',
                'job_id': result.get('job_id')
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', '打印失败')}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/printer-status')
@login_required
def api_printer_status():
    """Get printer status."""
    printer_name = request.args.get('printer')
    if not printer_name:
        return jsonify({'success': False, 'error': 'No printer specified'}), 400

    status = printer_manager.get_printer_status(printer_name)
    return jsonify(status)


@app.route('/printers')
@login_required
def printers_page():
    """Printer management page."""
    printers = printer_manager.get_printers()
    return render_template('printers.html', printers=printers)


@app.route('/history')
@login_required
def print_history_page():
    """Print history page."""
    return render_template('history.html')


@app.route('/history', methods=['POST'])
@login_required
def clear_history():
    """Clear print history (admin only)."""
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin only'}), 403
    # For now, just return success (full implementation would delete records)
    return jsonify({'success': True})


# ============ New API Endpoints ============

@app.route('/api/activation-codes', methods=['GET', 'POST'])
@admin_required
def api_activation_codes():
    """Manage activation codes."""
    if request.method == 'POST':
        data = request.get_json() or {}
        expires_days = data.get('expires_in_days', 7)
        created_by = session.get('user_id', 'admin')
        code_info = generate_code(created_by, expires_days)
        return jsonify(code_info)

    # GET - list all codes
    include_used = request.args.get('include_used', 'false').lower() == 'true'
    codes = list_codes(include_used=include_used)
    return jsonify(codes)


@app.route('/api/activation-codes', methods=['DELETE'])
@admin_required
def api_delete_activation_code():
    """Delete an activation code."""
    code = request.args.get('code')
    if not code:
        return jsonify({'success': False, 'error': 'Code required'}), 400

    deleted = db_delete_code(code)
    return jsonify({'success': deleted})


@app.route('/api/users', methods=['GET'])
@admin_required
def api_users():
    """List all users (admin only)."""
    users = db_list_users()
    return jsonify(users)


@app.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change current user's password."""
    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    if not old_password or not new_password:
        return jsonify({'success': False, 'error': '请填写所有字段'}), 400
    if len(new_password) < 4:
        return jsonify({'success': False, 'error': '新密码至少4位'}), 400
    result = user_manager.change_password(session['user_id'], old_password, new_password)
    return jsonify(result)


@app.route('/api/admin-reset-password', methods=['POST'])
@admin_required
def api_admin_reset_password():
    """Admin force-reset a user's password."""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    new_password = data.get('new_password', '')
    if not username or not new_password:
        return jsonify({'success': False, 'error': '请填写所有字段'}), 400
    if len(new_password) < 4:
        return jsonify({'success': False, 'error': '新密码至少4位'}), 400
    result = user_manager.admin_reset_password(username, new_password)
    return jsonify(result)


@app.route('/api/print-stats', methods=['GET'])
@login_required
def api_print_stats():
    """Get print statistics."""
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    user_id = request.args.get('user')
    printer_name = request.args.get('printer')

    stats = get_print_stats(
        from_date=from_date,
        to_date=to_date,
        user_id=user_id,
        printer_name=printer_name
    )
    return jsonify(stats)


@app.route('/api/print-history', methods=['GET'])
@login_required
def api_print_history():
    """Get print history for current user."""
    user_id = session.get('user_id')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    history = get_print_history(limit=limit, offset=offset)

    return jsonify(history)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)