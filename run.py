from pharmaweb import create_app

print("### EXECTUTION DU TEST DE MON APP###")
# Crée l'instance Flask en passant la configuration
main = create_app(config_class='config.Config')  # Adaptez ceci à votre classe de config réelle