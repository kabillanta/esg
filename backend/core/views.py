from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer

class DemoTokenView(APIView):
    """
    Provides a JWT for the requested role (admin or analyst) for demo purposes.
    Expects {'role': 'ADMIN' | 'ANALYST'} in the request body.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        role = request.data.get('role', 'ANALYST')
        
        # Try to find the pre-seeded user with this role
        user = User.objects.filter(role=role).first()
        
        if not user:
            return Response({'error': f'No user found with role {role}'}, status=404)
            
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })

class UserMeView(APIView):
    """
    Returns the currently authenticated user's details.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
