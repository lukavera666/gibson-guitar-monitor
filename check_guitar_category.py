import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import re

# CONFIGURACIÓN - Página de categoría y modelo buscado
CATEGORY_URL = "https://www.gibson.com/es-eu/collections/gibson-sg-electric-guitars"
SEARCH_KEYWORDS = ["standard", "61"]  # PRUEBA - buscar cualquier SG Standard 61
GUITAR_NAME = "Gibson SG Standard '61"

def check_category_for_guitar():
    """Busca la guitarra específica en la página de categoría"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        print(f"🔍 Buscando en página de categoría: {CATEGORY_URL}")
        response = requests.get(CATEGORY_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        
        print(f"📄 Página cargada correctamente")
        print(f"📏 Tamaño del contenido: {len(page_text)} caracteres")
        
        # Buscar todos los enlaces de productos
        all_links = soup.find_all('a', href=True)
        print(f"🔗 Total de enlaces encontrados: {len(all_links)}")
        
        found_guitars = []
        
        for link in all_links:
            link_text = link.get_text().lower()
            link_href = link['href'].lower()
            
            # Verificar si el enlace contiene las palabras clave
            matches_keywords = all(keyword in link_text or keyword in link_href 
                                  for keyword in SEARCH_KEYWORDS)
            
            if matches_keywords and '/products/' in link_href:
                # Construir URL completa
                if link_href.startswith('/'):
                    product_url = f"https://www.gibson.com{link['href']}"
                elif link_href.startswith('http'):
                    product_url = link['href']
                else:
                    continue
                
                # Obtener nombre del producto
                product_name = link.get_text(strip=True)
                if not product_name:
                    # Intentar extraer del href
                    product_name = link['href'].split('/')[-1].replace('-', ' ').title()
                
                # Evitar duplicados
                if any(g['url'] == product_url for g in found_guitars):
                    continue
                
                guitar_info = {
                    'name': product_name,
                    'url': product_url,
                    'available': True  # Asumimos disponible si aparece en la página
                }
                
                found_guitars.append(guitar_info)
                print(f"\n✨ Guitarra encontrada:")
                print(f"   ├─ Nombre: {product_name}")
                print(f"   ├─ URL: {product_url}")
                print(f"   └─ Disponible: True")
        
        print(f"\n📊 Resumen:")
        print(f"   └─ Guitarras encontradas: {len(found_guitars)}")
        
        return found_guitars if found_guitars else []
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return []

def send_email(guitars):
    """Envía un email con la lista de guitarras disponibles"""
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
        
        if len(guitars) == 1:
            message['Subject'] = f"🎸 ¡{GUITAR_NAME} DISPONIBLE en Gibson!"
        else:
            message['Subject'] = f"🎸 ¡{len(guitars)} Guitarras SG DISPONIBLES en Gibson!"
        
        guitar_list_html = ""
        guitar_list_text = ""
        
        for i, guitar in enumerate(guitars, 1):
            guitar_list_html += f"""
            <div style="background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #FF6B35; border-radius: 5px;">
                <h3 style="margin-top: 0; color: #333;">{i}. {guitar['name']}</h3>
                <a href="{guitar['url']}" 
                   style="background-color: #FF6B35; color: white; padding: 10px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 10px;">
                  VER GUITARRA
                </a>
            </div>
            """
            
            guitar_list_text += f"\n{i}. {guitar['name']}\n   🔗 {guitar['url']}\n"
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
              <h1 style="color: #FF6B35; margin-bottom: 20px;">🎸 ¡Guitarras Disponibles!</h1>
              
              <p style="color: #666; font-size: 16px;">Se han encontrado <strong>{len(guitars)} guitarra(s)</strong> que coinciden con tu búsqueda en la página de Gibson:</p>
              
              {guitar_list_html}
              
              <p style="color: #999; font-size: 14px; text-align: center; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                ⚡ Date prisa, las guitarras Gibson se agotan rápidamente<br>
                <small>Este mensaje fue enviado automáticamente por Gibson Guitar Monitor (Categoría)</small><br>
                <small>Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</small>
              </p>
            </div>
          </body>
        </html>
        """
        
        text_body = f"""
        ¡BUENAS NOTICIAS! 🎸
        
        Se han encontrado {len(guitars)} guitarra(s) disponible(s) en Gibson:
        {guitar_list_text}
        
        ¡Date prisa antes de que se agoten!
        
        ---
        Este mensaje fue enviado automáticamente por Gibson Guitar Monitor (Categoría)
        Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """
        
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        message.attach(part1)
        message.attach(part2)
        
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
    print(f"🎸 GIBSON GUITAR MONITOR - BÚSQUEDA EN CATEGORÍA")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*70 + "\n")
    
    print(f"🎯 Buscando: {GUITAR_NAME}")
    print(f"🔍 Palabras clave: {', '.join(SEARCH_KEYWORDS)}")
    print(f"🌐 Categoría: {CATEGORY_URL}\n")
    
    available_guitars = check_category_for_guitar()
    
    print("\n" + "-"*70)
    
    if available_guitars and len(available_guitars) > 0:
        print(f"\n🎉 ¡ENCONTRADA(S) {len(available_guitars)} GUITARRA(S) DISPONIBLE(S)!")
        print("📧 Enviando notificación por email...")
        
        if send_email(available_guitars):
            print("✅ Notificación enviada con éxito")
        else:
            print("⚠️ No se pudo enviar la notificación")
    else:
        print("\n😔 No se encontró la guitarra en la categoría")
        print("🔄 Se volverá a comprobar en la próxima ejecución programada")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
