from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.compiler.services.executor import CodeExecutorService

class CodeExecutionView(APIView):
    def post(self, request):
        code = request.data.get("code")
        language = request.data.get("language", "python")
        input_data = request.data.get("input_data", "")

        if not code:
            return Response({"error": "No code provided"}, status=status.HTTP_400_BAD_REQUEST)

        result = CodeExecutorService.execute(language, code, input_data)
        
        # If the result has an exit_code of 124, it's a timeout, but we still return 200 OK with the result
        return Response(result, status=status.HTTP_200_OK)
