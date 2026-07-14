class HistorySearchService:
    def __init__(self, event_service):
        self.event_srv = event_service

    def condition_filter(self, **kwargs):
        return self.event_srv.filter_events(**kwargs)