from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import requests
from django.conf import settings

# 🔥 SIMPLE JWT
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

# MODELOS DEL CORE
from core_users.models import CustomUser, UserProfile

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def google_login(request):
    """
    Login con Google - Implementación segura con JWT
    """
    try:
        print("🔐 [BACKEND] === INICIANDO GOOGLE LOGIN CON JWT ===")
        
        access_token = request.data.get('access_token')
        print(f"🔐 [BACKEND] Token recibido: {access_token[:20] if access_token else 'NONE'}...")
        
        if not access_token:
            return Response(
                {'error': 'access_token es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # DETERMINAR el tipo de token
        is_jwt = access_token.startswith('eyJ')  # Los JWT empiezan con eyJ
        
        if is_jwt:
            print("🔐 [BACKEND] Token detectado como JWT de Google")
            return handle_jwt_token(access_token)
        else:
            print("🔐 [BACKEND] Token detectado como Access Token de OAuth2")
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
    """Manejar Access Token de OAuth2 con verificación robusta"""
    try:
        # Verificar el token con Google
        google_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        print(f"📡 [BACKEND] Respuesta de Google: {google_response.status_code}")
        
        if google_response.status_code != 200:
            error_detail = google_response.json().get('error_description', 'Token inválido')
            return Response(
                {'error': f'Token de Google rechazado: {error_detail}'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        google_data = google_response.json()
        return create_or_get_user(google_data)
        
    except requests.exceptions.Timeout:
        print("❌ [BACKEND] Timeout verificando token con Google")
        return Response(
            {'error': 'Timeout verificando token con Google'}, 
            status=status.HTTP_408_REQUEST_TIMEOUT
        )
    except Exception as e:
        print(f"❌ [BACKEND] Error con access token: {str(e)}")
        return Response(
            {'error': f'Error verificando token: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

def handle_jwt_token(jwt_token: str):
    """Manejar JWT Token de Google Sign-In con verificación robusta"""
    try:
        # Verificar JWT con Google
        google_response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': jwt_token},
            timeout=10
        )
        
        print(f"📡 [BACKEND] Respuesta de Google JWT: {google_response.status_code}")
        
        if google_response.status_code != 200:
            error_detail = google_response.json().get('error_description', 'JWT inválido')
            return Response(
                {'error': f'JWT de Google rechazado: {error_detail}'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        google_data = google_response.json()
        return create_or_get_user(google_data)
        
    except requests.exceptions.Timeout:
        print("❌ [BACKEND] Timeout verificando JWT con Google")
        return Response(
            {'error': 'Timeout verificando JWT con Google'}, 
            status=status.HTTP_408_REQUEST_TIMEOUT
        )
    except Exception as e:
        print(f"❌ [BACKEND] Error con JWT: {str(e)}")
        return Response(
            {'error': f'Error verificando JWT: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

def create_or_get_user(google_data: dict):
    """Crear o obtener usuario basado en datos de Google - IMPLEMENTACIÓN SEGURA"""
    email = google_data.get('email')
    
    if not email:
        return Response(
            {'error': 'No se pudo obtener el email de Google'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 🔥 VALIDACIONES ADICIONALES DE SEGURIDAD
    email_verified = google_data.get('email_verified', False)
    if not email_verified:
        return Response(
            {'error': 'Email de Google no verificado'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Intentar obtener usuario existente
        user = CustomUser.objects.get(email=email)
        created = False
        print(f"✅ [BACKEND] Usuario existente encontrado: {email}")
        
    except CustomUser.DoesNotExist:
        # Crear nuevo usuario con datos validados
        user = CustomUser.objects.create(
            email=email,
            first_name=google_data.get('given_name', ''),
            last_name=google_data.get('family_name', ''),
            is_active=True
        )
        created = True
        print(f"🎉 [BACKEND] Nuevo usuario creado: {email}")
        
        # CREAR PERFIL AUTOMÁTICAMENTE
        UserProfile.objects.create(user=user)
        print(f"📝 [BACKEND] Perfil creado para: {email}")
    
    # 🔥 GENERAR TOKENS JWT SEGUROS
    try:
        refresh = RefreshToken.for_user(user)
        
        # 🔥 INFORMACIÓN ADICIONAL DE SEGURIDAD EN EL TOKEN
        refresh['email'] = user.email
        refresh['user_id'] = user.id
        
        print(f"✅ [BACKEND] Login JWT exitoso para: {email}")
        
        return Response({
            'key': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_verified': user.is_verified,
            },
            'token_type': 'Bearer',
            'expires_in': 1800,  # 30 minutos en segundos
            'created': created
        }, status=status.HTTP_200_OK)
        
    except TokenError as e:
        print(f"❌ [BACKEND] Error generando token JWT: {str(e)}")
        return Response(
            {'error': 'Error generando token de acceso'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    """
    Logout - Invalidar refresh token (seguridad mejorada)
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()  # 🔥 REVOCACIÓN INMEDIATA
            print("✅ [BACKEND] Refresh token revocado")
        
        return Response({
            'message': 'Logout exitoso'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"⚠️ [BACKEND] Error en logout: {str(e)}")
        # Aún retornamos éxito para no revelar información
        return Response({
            'message': 'Logout completado'
        }, status=status.HTTP_200_OK)