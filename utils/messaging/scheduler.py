from pythonosc import udp_client, osc_message_builder, dispatcher, osc_server
from uuid import uuid4
import threading
import time
from tqdm import tqdm
import heapq

class EventBuilder:
    def __init__(self, scheduler: 'Scheduler', event_type: str, uid: str, synth_name: str, start: float, params: dict):
        self.scheduler = scheduler
        self.event_type = event_type
        self.uid = str(uuid4()).replace('-', '') if uid is None else uid
        self.synth_name = synth_name
        self.start = start
        self.params = params
        self._add_event()
            
    def _add_event(self):
        args = [str(self), self.synth_name, self.start] + [item for sublist in self.params.items() for item in sublist]
        event_type = self.event_type
        heapq.heappush(self.scheduler.events, (self.start, (event_type, args)))
        self.scheduler.total_events += 1
    
    def __str__(self):
        return self.uid
        
    def __repr__(self):
        return self.uid

class SchedulerClient:
    def __init__(self, ip:str='127.0.0.1', send_port:int=9000):
        self.client = udp_client.SimpleUDPClient(ip, send_port)
        
    def new_synth(self, synth_name:str = None, start:float = 0, **params):
        uid = str(uuid4()).replace('-', '')
        msg = osc_message_builder.OscMessageBuilder(address='/new_synth')
        msg.add_arg(uid)
        msg.add_arg(synth_name)
        msg.add_arg(start)
        for key, value in params.items():
            msg.add_arg(key)
            msg.add_arg(value)
        self.client.send(msg.build())
        return uid

    def set_synth(self, uid:str, start:float, **params):
        msg = osc_message_builder.OscMessageBuilder(address='/set_synth')
        msg.add_arg(uid)
        msg.add_arg(start)
        for key, value in params.items():
            msg.add_arg(key)
            msg.add_arg(value)
        self.client.send(msg.build())
    
    def clear_events(self):
        self.client.send(osc_message_builder.OscMessageBuilder(address='/clear_events').build())
    
    def start(self):
        self.client.send(osc_message_builder.OscMessageBuilder(address='/start').build())
        
    def reset(self):
        self.client.send(osc_message_builder.OscMessageBuilder(address='/reset').build())

class Scheduler:
    def __init__(self, ip:str='127.0.0.1', send_port:int=57121, receive_port:int=9000):
        self.client = udp_client.SimpleUDPClient(ip, send_port)
        self.events = []
        self.paused = True
        self.events_processed = 0
        self.total_events = 0
        self.events_sent = 0
        self.batch_size = 25

        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map("/pause", self.pause_handler)
        self.dispatcher.map("/resume", self.resume_handler)
        self.dispatcher.map("/event_processed", self.event_processed_handler)
        self.dispatcher.map("/reset", self.reset_handler)
        self.dispatcher.map("/start", self.start)
        self.dispatcher.map("/new_synth", self.new_synth_handler)
        self.dispatcher.map("/set_synth", self.set_synth_handler)
        self.dispatcher.map("/clear_events", self.clear_events)
        
        self.server = osc_server.ThreadingOSCUDPServer((ip, receive_port), self.dispatcher)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        # self.server_thread.start()
        self.send_progress = None
        self.process_progress = None
        
    def init_progress_bars(self):
        self.send_progress = tqdm(total=self.total_events, 
                                desc="Ready to send", 
                                unit="events",
                                position=0,
                                leave=False)
        
        self.process_progress = tqdm(total=self.total_events,
                                   desc="Ready to process",
                                   unit="events",
                                   position=1,
                                   leave=False)
    
    def reset_progress_bars(self):
        if self.send_progress:
            self.send_progress.clear()
            self.send_progress.reset(total=self.total_events)
            self.send_progress.set_description("Ready to send")
        if self.process_progress:
            self.process_progress.clear()
            self.process_progress.reset(total=self.total_events)
            self.process_progress.set_description("Ready to process")
        
    def pause_handler(self, address, *args):
        if not self.paused:
            self.paused = True
            if self.send_progress:
                self.send_progress.set_description("Paused sending")

    def resume_handler(self, address, *args):
        self.paused = False
        if self.send_progress:
            self.send_progress.set_description("Sending")

    def event_processed_handler(self, address, *args):
        self.events_processed += 1
        if self.process_progress:
            self.process_progress.update(1)
        if self.events_sent == self.total_events:
            if self.send_progress:
                self.send_progress.set_description("All Events Sent")
        if self.events_processed == self.total_events:
            if self.process_progress:
                self.process_progress.set_description("All Events Processed")

    def reset_handler(self, address, *args):
        self.events_processed = 0
        self.events_sent = 0
        self.paused = True
        self.reset_progress_bars()

    def new_synth(self, synth_name:str = None, start:float = 0, **params):
        return EventBuilder(self, 'new', None, synth_name, start, params).uid

    def set_synth(self, uid:str, start:float, **params):
        EventBuilder(self, 'set', uid, None, start, params)

    def new_synth_handler(self, address, uid, synth_name, start, *params):
        param_dict = {params[i]: params[i+1] for i in range(0, len(params), 2)}
        EventBuilder(self, 'new', uid, synth_name, float(start), param_dict)
        self.reset_progress_bars()
        
    def set_synth_handler(self, address, uid, start, *params):
        param_dict = {params[i]: params[i+1] for i in range(0, len(params), 2)}
        EventBuilder(self, 'set', uid, None, float(start), param_dict)
        self.reset_progress_bars()
        
    def start(self, address, *args):
        if self.events_sent == self.total_events:
            self.events_processed = 0
            self.events_sent = 0
            self.reset_progress_bars()
        self.paused = False
        self.send_progress.set_description("Sending")
        self.process_progress.set_description("Processing")
        self.send_events()

    def send_events(self):
        events = self.events.copy()
        while events:
            while self.paused:
                time.sleep(0.01)
            _, (event_type, content) = heapq.heappop(events)
            
            msg = osc_message_builder.OscMessageBuilder(address='/storeEvent')
            msg.add_arg(event_type)
            for item in content:
                msg.add_arg(item)
            self.client.send(msg.build())
            self.events_sent += 1
            self.send_progress.update(1)
            # self.process_progress.total = self.events_sent
            # self.process_progress.refresh()
            time.sleep(0.01)

        eot_msg = osc_message_builder.OscMessageBuilder(address='/storeEvent')
        eot_msg.add_arg('end_of_transmission')
        self.client.send(eot_msg.build())
        self.send_progress.set_description("All Events Sent")

    def clear_events(self):
        self.events = []
        self.total_events = 0
        self.events_processed = 0
        self.events_sent = 0
        self.paused = True
        self.reset_progress_bars()

    def stop_server(self):
        self.server.shutdown()
        self.server_thread.join()
        # exit(0)

    def run(self):
        self.server_thread.start()
        self.init_progress_bars()
        # self.send_events()
        # self.stop_server()

if __name__ == '__main__':
    print('Scheduler server initialized and running...')
    scheduler = Scheduler()
    scheduler.run()
    # scheduler.init_progress_bars()
    # scheduler.server_thread.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down scheduler server...")
        scheduler.stop_server()