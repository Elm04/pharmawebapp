from pharmaweb import mainapp

# Crée l'application en mode production
app = mainapp()

if __name__ == "__main__":
    # Pour le développement local seulement
    from config import Config
    app = mainapp(Config)
    app.run()