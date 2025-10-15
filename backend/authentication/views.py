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
    Login con Google - Soporta JWT y Access Token
    """
    try:
        print("🔐 [BACKEND] === INICIANDO GOOGLE LOGIN ===")
        
        access_token = request.data.get('access_token')
        print(f"🔐 [BACKEND] Token recibido: {access_token[:50] if access_token else 'NONE'}...")
        
        if not access_token:
            return Response(
                {'error': 'access_token es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # DETERMINAR el tipo de token
        is_jwt = access_token.startswith('eyJ')  # Los JWT empiezan con eyJ
        
        if is_jwt:
            print("🔐 [BACKEND] Token detectado como JWT")
            return handle_jwt_token(access_token)
        else:
            print("🔐 [BACKEND] Token detectado como Access Token")
            return handle_access_token(access_token)
        
    except Exception as e:
        print(f"❌ [BACKEND] Error en google_login: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error en autenticación: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

def handle_access_token(access_token: str):
    """Manejar Access Token de OAuth2"""
    try:
        # Verificar el token con Google
        google_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        print(f"📡 [BACKEND] Respuesta de Google: {google_response.status_code}")
        
        if google_response.status_code != 200:
            return Response(
                {'error': f'Token de Google inválido: {google_response.text}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        google_data = google_response.json()
        return create_or_get_user(google_data)
        
    except Exception as e:
        print(f"❌ [BACKEND] Error con access token: {str(e)}")
        return Response(
            {'error': f'Error verificando token: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

def handle_jwt_token(jwt_token: str):
    """Manejar JWT Token de Google Sign-In"""
    try:
        # Verificar JWT con Google
        google_response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': jwt_token},
            timeout=10
        )
        
        print(f"📡 [BACKEND] Respuesta de Google JWT: {google_response.status_code}")
        
        if google_response.status_code != 200:
            return Response(
                {'error': f'JWT de Google inválido: {google_response.text}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        google_data = google_response.json()
        return create_or_get_user(google_data)
        
    except Exception as e:
        print(f"❌ [BACKEND] Error con JWT: {str(e)}")
        return Response(
            {'error': f'Error verificando JWT: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

def create_or_get_user(google_data: dict):
    """Crear o obtener usuario basado en datos de Google"""
    email = google_data.get('email')
    
    if not email:
        return Response(
            {'error': 'No se pudo obtener el email de Google'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from django.contrib.auth.models import User
    from rest_framework.authtoken.models import Token
    
    user, created = User.objects.get_or_create(
        username=email,
        defaults={
            'email': email,
            'first_name': google_data.get('given_name', ''),
            'last_name': google_data.get('family_name', ''),
            'is_active': True
        }
    )
    
    token, _ = Token.objects.get_or_create(user=user)
    
    print(f"✅ [BACKEND] Login exitoso para: {email}")
    
    return Response({
        'key': token.key,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        }
    })