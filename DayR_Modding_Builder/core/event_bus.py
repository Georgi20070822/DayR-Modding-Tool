class EventBus:
    """Простая событийная шина (паттерн Observer)"""
    
    _subscribers = {}
    
    @classmethod
    def subscribe(cls, event_type, callback):
        """Подписаться на событие"""
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(callback)
    
    @classmethod
    def unsubscribe(cls, event_type, callback):
        """Отписаться от события"""
        if event_type in cls._subscribers:
            cls._subscribers[event_type].remove(callback)
    
    @classmethod
    def publish(cls, event_type, data=None):
        """Опубликовать событие"""
        if event_type in cls._subscribers:
            for callback in cls._subscribers[event_type]:
                callback(data)
    
    @classmethod
    def clear(cls):
        """Очистить все подписки"""
        cls._subscribers.clear()