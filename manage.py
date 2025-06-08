#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    # 'config.settings' 부분이 자신의 프로젝트 설정 파일 경로와 맞는지 확인하세요.
    # 보통 프로젝트 이름(또는 설정 앱 이름) + .settings 입니다.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OpenWallets.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()