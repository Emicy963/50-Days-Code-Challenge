import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

# Configurar logger específico para tempos de requisição
logger = logging.getLogger('request_time')

class RequestTimeMiddleware(MiddlewareMixin):
    """
    Middleware para calcular e registrar o tempo de processamento das requisições.
    
    Funcionalidades:
    - Calcula o tempo total de processamento
    - Registra logs detalhados (opcional)
    - Adiciona headers de resposta com informações de timing
    - Suporte a diferentes níveis de logging
    """
    
    def process_request(self, request):
        """
        Executado no início de cada requisição.
        Registra o timestamp de início.
        """
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """
        Executado após o processamento da view.
        Calcula o tempo decorrido e adiciona informações à resposta.
        """
        if hasattr(request, '_start_time'):
            # Calcular tempo de processamento
            end_time = time.time()
            processing_time = end_time - request._start_time
            
            # Adicionar header com tempo de processamento (em milissegundos)
            response['X-Processing-Time'] = f'{processing_time * 1000:.2f}ms'
            
            # Adicionar timestamp de processamento
            response['X-Processing-Timestamp'] = str(int(end_time))
            
            # Registrar log se habilitado
            self._log_request_time(request, processing_time)
            
            # Verificar se o tempo excede o limite configurado
            self._check_slow_request(request, processing_time)
        
        return response
    
    def process_exception(self, request, exception):
        """
        Executado quando uma exceção ocorre durante o processamento.
        Ainda calcula o tempo mesmo em caso de erro.
        """
        if hasattr(request, '_start_time'):
            end_time = time.time()
            processing_time = end_time - request._start_time
            
            # Log específico para requisições com erro
            logger.error(
                f"EXCEPTION - {request.method} {request.path} - "
                f"Time: {processing_time * 1000:.2f}ms - "
                f"Exception: {type(exception).__name__}: {str(exception)}"
            )
        
        return None
    
    def _log_request_time(self, request, processing_time):
        """
        Registra logs detalhados da requisição.
        """
        # Verificar se o logging está habilitado nas configurações
        if getattr(settings, 'LOG_REQUEST_TIME', True):
            time_ms = processing_time * 1000
            
            # Obter informações adicionais da requisição
            user_info = getattr(request.user, 'username', 'Anonymous') if hasattr(request, 'user') else 'Unknown'
            remote_addr = self._get_client_ip(request)
            
            # Log básico
            log_message = (
                f"{request.method} {request.path} - "
                f"Time: {time_ms:.2f}ms - "
                f"User: {user_info} - "
                f"IP: {remote_addr}"
            )
            
            # Adicionar parâmetros GET se existirem
            if request.GET:
                log_message += f" - GET: {dict(request.GET)}"
            
            # Determinar nível do log baseado no tempo
            if time_ms > getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1000):
                logger.warning(f"SLOW REQUEST - {log_message}")
            elif time_ms > 500:
                logger.info(f"MEDIUM REQUEST - {log_message}")
            else:
                logger.debug(f"FAST REQUEST - {log_message}")
    
    def _check_slow_request(self, request, processing_time):
        """
        Verifica se a requisição excedeu o limite de tempo configurado.
        """
        threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1000) / 1000  # Converter ms para segundos
        
        if processing_time > threshold:
            # Log de alerta para requisições muito lentas
            logger.warning(
                f"SLOW REQUEST ALERT - {request.method} {request.path} - "
                f"Time: {processing_time * 1000:.2f}ms (threshold: {threshold * 1000}ms)"
            )
            
            # Opcional: Enviar notificação ou métrica para sistema de monitoramento
            self._handle_slow_request_alert(request, processing_time)
    
    def _handle_slow_request_alert(self, request, processing_time):
        """
        Método para lidar com alertas de requisições lentas.
        Pode ser estendido para integrar com sistemas de monitoramento.
        """
        # Placeholder para integração com sistemas de monitoramento
        # Exemplos: Sentry, New Relic, DataDog, etc.
        pass
    
    def _get_client_ip(self, request):
        """
        Obtém o IP real do cliente, considerando proxies e load balancers.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip


class SimpleRequestTimeMiddleware(MiddlewareMixin):
    """
    Versão simplificada do middleware de tempo de requisição.
    Use esta versão se você quiser apenas o header de resposta sem logs detalhados.
    """
    
    def process_request(self, request):
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            processing_time = time.time() - request._start_time
            response['X-Processing-Time'] = f'{processing_time * 1000:.2f}ms'
        return response
