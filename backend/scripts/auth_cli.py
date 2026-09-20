#!/usr/bin/env python
"""auth_cli.py — CLI tool for User Management and JWT Authentication.

Commands:
  register        Register a new user in the database.
  login           Authenticate credentials and return a signed JWT token.
  verify-token    Inspect and validate a JWT access token.
  list-users      List registered users.

Examples:
  python scripts/auth_cli.py register --email alice@example.com --password Secret123! --name "Alice"
  python scripts/auth_cli.py login --email alice@example.com --password Secret123!
  python scripts/auth_cli.py verify-token --token <JWT_TOKEN>
  python scripts/auth_cli.py list-users
  python scripts/auth_cli.py login --email alice@example.com --password Secret123! --json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Silence sqlalchemy query logging on CLI stdout
for name in ("sqlalchemy", "sqlalchemy.engine", "sqlalchemy.engine.Engine", "sqlalchemy.pool", "sqlalchemy.dialects"):
    lg = logging.getLogger(name)
    lg.handlers.clear()
    lg.propagate = False
    lg.setLevel(logging.ERROR)

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.security import create_access_token, decode_access_token
from app.db.session import SessionLocal, engine
from app.models.user import User
from app.schemas.auth import UserRegisterRequest
from app.services.auth_service import auth_service

engine.echo = False
for name in ("sqlalchemy", "sqlalchemy.engine", "sqlalchemy.engine.Engine", "sqlalchemy.pool", "sqlalchemy.dialects"):
    lg = logging.getLogger(name)
    lg.handlers.clear()
    lg.propagate = False
    lg.setLevel(logging.ERROR)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="User Management & JWT Authentication CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # register
    reg_parser = subparsers.add_parser("register", help="Register a new user")
    reg_parser.add_argument("--email", required=True, help="User email address")
    reg_parser.add_argument("--password", required=True, help="Password (min 8 chars)")
    reg_parser.add_argument("--name", default=None, help="Full name")
    reg_parser.add_argument("--superuser", action="store_true", help="Create as superuser")

    # login
    login_parser = subparsers.add_parser("login", help="Login and obtain a JWT access token")
    login_parser.add_argument("--email", required=True, help="User email address")
    login_parser.add_argument("--password", required=True, help="User password")

    # verify-token
    vt_parser = subparsers.add_parser("verify-token", help="Verify and decode a JWT token")
    vt_parser.add_argument("--token", required=True, help="JWT access token string")

    # list-users
    subparsers.add_parser("list-users", help="List all registered users")

    return parser


def handle_register(args: argparse.Namespace) -> int:
    db = SessionLocal()
    try:
        req = UserRegisterRequest(
            email=args.email,
            password=args.password,
            full_name=args.name,
        )
        user = auth_service.register_user(db, req=req)
        if args.superuser:
            user.is_superuser = True
            db.commit()
            db.refresh(user)
        if args.json:
            print(json.dumps({
                "status": "success",
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
            }, indent=2))
        else:
            print(f"[OK] User created successfully: ID={user.id}, Email={user.email}, Superuser={user.is_superuser}")
        return 0
    except ValueError as err:
        if args.json:
            print(json.dumps({"status": "error", "message": str(err)}, indent=2))
        else:
            print(f"[ERROR] Registration failed: {err}")
        return 1
    finally:
        db.close()


def handle_login(args: argparse.Namespace) -> int:
    db = SessionLocal()
    try:
        user = auth_service.authenticate(db, email=args.email, password=args.password)
        if not user:
            if args.json:
                print(json.dumps({"status": "error", "message": "Invalid email or password"}, indent=2))
            else:
                print("[ERROR] Authentication failed: Invalid email or password")
            return 1

        token = create_access_token(subject=user.id)
        if args.json:
            print(json.dumps({
                "status": "success",
                "access_token": token,
                "token_type": "bearer",
                "user_id": user.id,
                "email": user.email,
            }, indent=2))
        else:
            print(f"[OK] Logged in successfully as {user.email}")
            print(f"Token: {token}")
        return 0
    finally:
        db.close()


def handle_verify_token(args: argparse.Namespace) -> int:
    try:
        payload = decode_access_token(args.token)
        if args.json:
            print(json.dumps({"status": "valid", "payload": payload}, indent=2))
        else:
            print("[OK] Token is valid!")
            print(f"  Subject (User ID): {payload.get('sub')}")
            print(f"  Token Type:        {payload.get('type')}")
            print(f"  Expires At:        {payload.get('exp')}")
        return 0
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "invalid", "error": str(exc)}, indent=2))
        else:
            print(f"[ERROR] Invalid or expired token: {exc}")
        return 1


def handle_list_users(args: argparse.Namespace) -> int:
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if args.json:
            data = [
                {
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "is_active": u.is_active,
                    "is_superuser": u.is_superuser,
                }
                for u in users
            ]
            print(json.dumps(data, indent=2))
        else:
            print(f"Found {len(users)} registered users:")
            for u in users:
                role = "Admin" if u.is_superuser else "User"
                status = "Active" if u.is_active else "Inactive"
                print(f"  [{u.id}] {u.email} ({u.full_name or 'N/A'}) - {role}, {status}")
        return 0
    finally:
        db.close()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "register":
        return handle_register(args)
    elif args.command == "login":
        return handle_login(args)
    elif args.command == "verify-token":
        return handle_verify_token(args)
    elif args.command == "list-users":
        return handle_list_users(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
