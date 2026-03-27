import os
import subprocess
import sys

def run_cmd(cmd, env=None):
    print(f"Running: {cmd}")
    env_vars = os.environ.copy()
    env_vars['PYTHONUTF8'] = '1' # Fix Windows charmap encoding for Unicode characters
    if env:
        env_vars.update(env)
    result = subprocess.run(cmd, env=env_vars, shell=True)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(1)

def main():
    print("--- 1. Dumping Categories from Production DB (Render Postgres) ---")
    run_cmd(r".\env\Scripts\python manage.py dumpdata ecommerce_app.Category --indent 4 > uat_categories.json")

    print("\n--- 2. Dumping Products from Production DB (Render Postgres) ---")
    run_cmd(r".\env\Scripts\python manage.py dumpdata ecommerce_app.Product --indent 4 > uat_products.json")

    print("\n--- 3. Initializing new UAT SQLite Database (uat_db.sqlite3) ---")
    # Tell Django to use the UAT database for all subsequent commands
    uat_env = {'USE_UAT_DB': '1'}
    run_cmd(r".\env\Scripts\python manage.py migrate", env=uat_env)

    print("\n--- 4. Loading Categories and Products into UAT DB ---")
    run_cmd(r".\env\Scripts\python manage.py loaddata uat_categories.json", env=uat_env)
    run_cmd(r".\env\Scripts\python manage.py loaddata uat_products.json", env=uat_env)

    print("\n[SUCCESS] UAT Setup Complete! Created uat_db.sqlite3 and loaded product data.")
    print("Next step: Run 'python generate_uat_data.py 100'")

if __name__ == "__main__":
    main()
