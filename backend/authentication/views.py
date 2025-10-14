from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import requests
from django.conf import settings
import json

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def google_login(request):
    """
    Login con Google - Endpoint personalizado
    """
    try:
        print("🔐 [BACKEND] === INICIANDO GOOGLE LOGIN ===")
        print(f"🔐 [BACKEND] Método: {request.method}")
        print(f"🔐 [BACKEND] Headers: {dict(request.headers)}")
        
        # Verificar el body
        body_content = request.body.decode('utf-8') if request.body else 'EMPTY'
        print(f"🔐 [BACKEND] Body contenido: {body_content}")
        
        # Intentar parsear el JSON de diferentes formas
        access_token = None
        try:
            if request.body:
                body_data = json.loads(request.body)
                access_token = body_data.get('access_token')
                print(f"🔐 [BACKEND] Token desde request.body: {access_token[:30] if access_token else 'NONE'}...")
        except json.JSONDecodeError as e:
            print(f"❌ [BACKEND] Error parseando request.body: {e}")
        
        # Intentar desde request.data
        if not access_token and hasattr(request, 'data'):
            access_token = request.data.get('access_token')
            print(f"🔐 [BACKEND] Token desde request.data: {access_token[:30] if access_token else 'NONE'}...")
        
        print(f"🔐 [BACKEND] Access token final: {access_token}")
        
        if not access_token:
            print("❌ [BACKEND] No se recibió access_token")
            return Response(
                {'error': 'access_token es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar el token con Google
        print("🌐 [BACKEND] Verificando token con Google...")
        try:
            google_response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                params={'access_token': access_token},
                timeout=10
            )
            
            print(f"📡 [BACKEND] Respuesta de Google - Status: {google_response.status_code}")
            print(f"📡 [BACKEND] Respuesta de Google - Headers: {dict(google_response.headers)}")
            
            if google_response.status_code != 200:
                print(f"❌ [BACKEND] Token inválido. Error: {google_response.text}")
                return Response(
                    {'error': f'Token de Google inválido: {google_response.text}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            google_data = google_response.json()
            print(f"✅ [BACKEND] Datos de Google: {google_data}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ [BACKEND] Error en petición a Google: {e}")
            return Response(
                {'error': f'Error conectando con Google: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        email = google_data.get('email')
        first_name = google_data.get('given_name', '')
        last_name = google_data.get('family_name', '')
        picture = google_data.get('picture', '')
        
        print(f"✅ [BACKEND] Usuario Google - Email: {email}, Nombre: {first_name} {last_name}")
        
        if not email:
            print("❌ [BACKEND] No se pudo obtener el email de Google")
            return Response(
                {'error': 'No se pudo obtener el email de Google'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar o crear usuario
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token
        
        print(f"👤 [BACKEND] Buscando/creando usuario: {email}")
        
        try:
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True
                }
            )
            
            # Actualizar información si el usuario ya existe
            if not created:
                user.first_name = first_name
                user.last_name = last_name
                user.save()
                print(f"✅ [BACKEND] Usuario actualizado: {user.email}")
            else:
                print(f"✅ [BACKEND] Usuario creado: {user.email}")
            
            # Crear o obtener token
            token, _ = Token.objects.get_or_create(user=user)
            
            print(f"✅ [BACKEND] Token generado: {token.key}")
            
            response_data = {
                'key': token.key,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'picture': picture
                }
            }
            
            print(f"✅ [BACKEND] === LOGIN EXITOSO ===")
            print(f"✅ [BACKEND] Enviando respuesta: {response_data}")
            
            return Response(response_data)
            
        except Exception as user_error:
            print(f"❌ [BACKEND] Error con usuario/token: {user_error}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Error creando usuario: {str(user_error)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        print("❌ [BACKEND] === ERROR GENERAL ===")
        print(f"❌ [BACKEND] Error: {str(e)}")
        import traceback
        print("❌ [BACKEND] Traceback:")
        traceback.print_exc()
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )