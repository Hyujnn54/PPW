"""
PPW – Personal Password Manager
Entry point: launches the GUI by default.
Use  --cli  flag for the command-line interface.
"""
import sys


def main():
    use_cli = "--cli" in sys.argv or "-c" in sys.argv

    if not use_cli:
        try:
            import gui_app as _gui
            _gui.main()
            return
        except ImportError:
            print("PyQt6 not found. Falling back to CLI. Install with: pip install PyQt6")
        except Exception as e:
            print(f"GUI error: {e}\nFalling back to CLI.")

    # ── CLI fallback ──────────────────────────────────────────────
    from db.database import db_manager
    from services.master_password_service import MasterPasswordService
    from services.account_service import AccountService
    from utils.encryption import PasswordGenerator
    import getpass

    def init():
        if not db_manager.connect():
            sys.exit("Cannot connect to MongoDB. Check your MONGO_URI in .env")
        db_manager.initialize_collections()

    def cli_loop():
        init()
        while True:
            print("\n1. Register  2. Login  3. Exit")
            choice = input("Choice: ").strip()
            if choice == "1":
                u = input("Username: ")
                p = getpass.getpass("Master password: ")
                ok, msg = MasterPasswordService.create_master_password(u, p)
                print(msg)
            elif choice == "2":
                u = input("Username: ")
                p = getpass.getpass("Master password: ")
                ok, user, msg = MasterPasswordService.verify_master_password(u, p)
                if not ok:
                    print(msg)
                    continue
                key = MasterPasswordService.get_encryption_key(user["user_id"], p)
                print(f"\nWelcome {user['username']}!")
                while True:
                    print("\n1. Add  2. List  3. Get password  4. Generate  5. Logout")
                    c = input("Choice: ").strip()
                    if c == "1":
                        t = input("Title: ")
                        pw = getpass.getpass("Password (blank=generate): ") or PasswordGenerator.generate_password()
                        AccountService.add_account(user["user_id"], key, t, pw,
                            input("Username: ") or None,
                            input("URL: ") or None)
                    elif c == "2":
                        for a in AccountService.get_all_accounts(user["user_id"]):
                            print(f"  {a['title']}  [{a['category']}]  strength:{a['strength_score']}")
                    elif c == "3":
                        t = input("Title: ")
                        results = AccountService.get_all_accounts(user["user_id"], search=t)
                        if results:
                            pw = AccountService.get_password(user["user_id"], results[0]["account_id"], key)
                            print(f"Password: {pw}")
                    elif c == "4":
                        pw = PasswordGenerator.generate_password(int(input("Length [16]: ") or 16))
                        score, fb = PasswordGenerator.calculate_strength(pw)
                        print(f"{pw}  ({score}/100 – {fb})")
                    elif c == "5":
                        break
            elif choice == "3":
                db_manager.disconnect()
                break

    try:
        cli_loop()
    except KeyboardInterrupt:
        print("\nBye!")
        db_manager.disconnect()


if __name__ == "__main__":
    main()
