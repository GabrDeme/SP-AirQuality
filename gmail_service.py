import smtplib
import os
from email.message import EmailMessage

def enviar_alerta(destinatarios, assunto, corpoHTML):
    
    remetente = "noreply.airqualitysp@gmail.com"
    senha_app = "audlnykjkgxeeuxx"
    
    msg = EmailMessage()
    msg['Subject'] = assunto
    msg['From'] = remetente
    msg['To'] = ', '.join(destinatarios)
    
    msg.add_alternative(corpoHTML, subtype='html')
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remetente, senha_app)
            smtp.send_message(msg)
        
        print(f"Alerta enviado com sucesso para: {', '.join(destinatarios)}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("Erro de autenticação.")
        return False
    except Exception as e:
        print(f"Ocorreu um erro ao enviar o e-mail: {e}")
        return False