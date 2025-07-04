from pharmaweb import mainapp

app = mainapp()

if __name__ =="__main__":
    app.run(debug=True, host="0.0.0.0")