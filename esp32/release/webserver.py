from machine import RTC

from microdot import Microdot
from microdot import send_file


app = Microdot()


@app.route('/static/<path:path>')
def static(request, path):
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
    return send_file('static/' + path)


@app.get('/')
def index(request):
    return send_file('/static/index.html')

@app.route('/time', methods=['GET', 'POST'])
def set_time(request):
    if request.method == 'POST':
        date = request.form.get('date').split('-')
        weekday = request.form.get('weekday')
        time = request.form.get('time').split(':')

        year = int(date[0])
        month = int(date[1])
        day = int(date[2])
        weekday = int(weekday)
        hour = int(time[0])
        minute = int(time[1])
        
        rtc = RTC()
        rtc.datetime((year, month, day, weekday, hour, minute, 0, 0))
        print("datetime:", rtc.datetime())
        return send_file('static/success.html')
    return send_file('/static/time.html')


@app.get('/shutdown')
def shutdown(request):
    request.app.shutdown()
    return 'The server is shutting down...'


class WebServer:
    def __init__(self, logger, memory):
        self.log = logger
        self.memory = memory
        
    def start(self):
        self.memory.clean_ram()
        self.log.info('Start Webserver')
        try:
            app.run(port=80, debug=True)
        except OSError as e:
            self.log.warning(e)
        self.memory.clean_ram()
        self.log.info('Shutdown Webserver')