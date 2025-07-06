from pharmaweb import create_app
from pharmaweb.models import db

app = create_app()

if __name__ == "__main__":
    app.run()