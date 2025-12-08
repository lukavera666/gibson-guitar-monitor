import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import time

# CONFIGURACIÓN DE LA GUITARRA
GUITAR_URL = "https://www.gibson.com/es-eu/products/gibson-sg-standard-61-ebony"
GUITAR_NAME = "Gibson SG Standard '61 Ebony"

def check_availability():
    """Comprueba si la guitarra está disponible en Gibson España"""
    try:
        return True
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        print(f"🔍 Comprobando disponibilidad en: {GUITAR_URL}")
        response = requests.get(GUITAR_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Estrategia 1: Buscar botón "Añadir al carrito" o "Add to cart"
        add_to_cart_button = soup.find('button', string=lambda x: x and any(
            phrase in x.lower() for phrase in ['añadir al carrito', 'add to cart', 'add to bag']
        ))
        
        # Estrategia 2: Buscar por clases comunes de botones de compra
        if not add_to_cart_button:
            add_to_cart_button = soup.find('button', class_=lambda x: x and any(
                cls in str(x).lower() for cls in ['add-to-cart', 'addtocart', 'btn-cart']
            ))
        
        # Estrategia 3: Buscar formularios de compra
        purchase_form = soup.find('form', class_=lambda x: x and 'cart' in str(x).lower())
        
        # Verificar si hay indicadores de "fuera de stock"
        out_of_stock_indicators = [
            'agotado', 'out of stock', 'sold out', 'no disponible',
            'not available', 'coming soon', 'próximamente'
        ]
        
        page_text = soup.get_text().lower()
        is_out_of_stock = any(indicator in page_text for indicator in out_of_stock_indicators)
        
        # La guitarra está disponible si:
        # - Hay botón de añadir al carrito O formulario de compra
        # - Y NO hay indicadores de "fuera de stock"
        is_available = (add_to_cart_button is not None or purchase_form is not None) and not is_out_of_stock
        
        print(f"📊 Resultados de la comprobación:")
        print(f"   ├─ Botón 'Añadir al carrito' encontrado: {add_to_cart_button is not None}")
        print(f"   ├─ Formulario de compra encontrado: {purchase_form is not None}")
        print(f"   ├─ Indicadores de 'fuera de stock': {is_out_of_stock}")
        print(f"   └─ ✅ DISPONIBLE: {is_available}")
        
        return is_available
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def send_email(guitar_name, guitar_url):
    """Envía un email de notificación cuando la guitarra está disponible"""
    try:
        sender_email = os.environ.get('EMAIL_USER')
        sender_password = os.environ.get('EMAIL_PASSWORD')
        receiver_email = os.environ.get('EMAIL_TO')
        
        if not all([sender_email, sender_password, receiver_email]):
            print("⚠️ Variables de entorno de email no configuradas")
            return False
        
        message = MIMEMultipart('alternative')
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = f"🎸 ¡{guitar_name} DISPONIBLE en Gibson!"
        
        # Crear versión HTML del email
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
              <h1 style="color: #FF6B35; margin-bottom: 20px;">🎸 ¡Guitarra Disponible!</h1>
              
              <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #FF6B35; margin: 20px 0;">
                <h2 style="margin-top: 0; color: #333;">{guitar_name}</h2>
                <p style="color: #666; font-size: 16px;">La guitarra que estabas esperando está de vuelta en stock en Gibson España.</p>
              </div>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="{guitar_url}" 
                   style="background-color: #FF6B35; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 18px;">
                  VER GUITARRA
                </a>
              </div>
              
              <p style="color: #999; font-size: 14px; text-align: center; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                ⚡ Date prisa, las guitarras Gibson se agotan rápidamente<br>
                <small>Este mensaje fue enviado automáticamente por Gibson Guitar Monitor</small>
              </p>
            </div>
          </body>
        </html>
        """
        
        # Versión texto plano
        text_body = f"""
        ¡BUENAS NOTICIAS! 🎸
        
        La guitarra que estabas esperando está disponible:
        
        🎸 {guitar_name}
        🔗 {guitar_url}
        
        ¡Date prisa antes de que se agote!
        
        ---
        Este mensaje fue enviado automáticamente por Gibson Guitar Monitor
        Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """
        
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        message.attach(part1)
        message.attach(part2)
        
        # Conectar y enviar
        print("📧 Conectando al servidor de email...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
            
        print(f"✅ Email enviado exitosamente a {receiver_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Error de autenticación. Verifica EMAIL_USER y EMAIL_PASSWORD")
        return False
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False

def main():
    print("\n" + "="*70)
    print(f"🎸 GIBSON GUITAR MONITOR")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*70 + "\n")
    
    print(f"🎯 Guitarra objetivo: {GUITAR_NAME}")
    print(f"🌐 URL: {GUITAR_URL}\n")
    
    is_available = check_availability()
    
    print("\n" + "-"*70)
    
    if is_available:
        print("\n🎉 ¡LA GUITARRA ESTÁ DISPONIBLE!")
        print("📧 Enviando notificación por email...")
        
        if send_email(GUITAR_NAME, GUITAR_URL):
            print("✅ Notificación enviada con éxito")
        else:
            print("⚠️ No se pudo enviar la notificación")
    else:
        print("\n😔 La guitarra todavía no está disponible")
        print("🔄 Se volverá a comprobar en la próxima ejecución programada")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
