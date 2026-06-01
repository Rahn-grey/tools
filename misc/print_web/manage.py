"""
PyPrint CLI — 命令行管理工具
用法: python manage.py <命令> [参数]
"""
import sys
import os
import secrets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_users import create_user, list_users, delete_user, change_password, admin_reset_password
from utils.database import init_db


def cmd_add_user():
    """添加用户: python manage.py adduser <用户名> <密码> [admin]"""
    if len(sys.argv) < 4:
        print('用法: python manage.py adduser <用户名> <密码> [admin]')
        print('示例: python manage.py adduser zhangsan mypass123')
        print('      python manage.py adduser zhangsan mypass123 admin')
        sys.exit(1)
    username = sys.argv[2]
    password = sys.argv[3]
    role = 'admin' if len(sys.argv) > 4 and sys.argv[4] == 'admin' else 'user'
    result = create_user(username, password, role=role)
    if 'error' in result:
        print(f'错误: {result["error"]}')
    else:
        print(f'用户 {username} ({role}) 创建成功')


def cmd_list_users():
    """列出所有用户: python manage.py listusers"""
    users = list_users()
    if not users:
        print('暂无用户')
        return
    print(f'{"用户名":<20} {"角色":<8} {"创建时间"}')
    print('-' * 50)
    for u in users:
        print(f'{u["username"]:<20} {u["role"]:<8} {u["created_at"]}')


def cmd_del_user():
    """删除用户: python manage.py deluser <用户名>"""
    if len(sys.argv) < 3:
        print('用法: python manage.py deluser <用户名>')
        sys.exit(1)
    username = sys.argv[2]
    if delete_user(username):
        print(f'用户 {username} 已删除')
    else:
        print(f'用户 {username} 不存在')


def cmd_chpass():
    """修改密码: python manage.py chpass <用户名>"""
    if len(sys.argv) < 3:
        print('用法: python manage.py chpass <用户名>')
        sys.exit(1)
    username = sys.argv[2]
    old = input(f'请输入 {username} 的旧密码: ').strip()
    new = input('请输入新密码（至少4位）: ').strip()
    if len(new) < 4:
        print('错误: 新密码至少4位')
        sys.exit(1)
    result = change_password(username, old, new)
    if result['success']:
        print('密码修改成功')
    else:
        print(f'错误: {result["error"]}')


def cmd_reset_pass():
    """管理员强制重置密码: python manage.py resetpass <用户名>"""
    if len(sys.argv) < 3:
        print('用法: python manage.py resetpass <用户名>')
        sys.exit(1)
    username = sys.argv[2]
    new = input(f'请输入 {username} 的新密码（至少4位，留空则随机生成）: ').strip()
    if not new:
        new = secrets.token_hex(4)
        print(f'已生成随机密码: {new}')
    if len(new) < 4:
        print('错误: 新密码至少4位')
        sys.exit(1)
    result = admin_reset_password(username, new)
    if result['success']:
        print(f'密码已重置，新密码: {new}')
    else:
        print(f'错误: {result["error"]}')


COMMANDS = {
    'adduser': cmd_add_user,
    'listusers': cmd_list_users,
    'deluser': cmd_del_user,
    'chpass': cmd_chpass,
    'resetpass': cmd_reset_pass,
}


def main():
    init_db()
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print('PyPrint 管理工具')
        print('')
        print('命令:')
        print('  adduser    <用户名> <密码> [admin]  添加用户')
        print('  listusers                            列出所有用户')
        print('  deluser    <用户名>                  删除用户')
        print('  chpass     <用户名>                  修改密码（需旧密码）')
        print('  resetpass  <用户名>                  强制重置密码（管理员）')
        sys.exit(1)
    COMMANDS[sys.argv[1]]()


if __name__ == '__main__':
    main()
