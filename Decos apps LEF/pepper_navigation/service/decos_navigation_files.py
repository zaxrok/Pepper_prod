#!/usr/bin/env python
import qi
import sys
import os

class DecosNavigationFiles:
    services_connected = None

    def __init__(self, application):
        # Getting a session that will be reused everywhere
        self.application = application
        self.session = application.session
        self.service_name = self.__class__.__name__

        # Getting a logger. Logs will be in /var/log/naoqi/servicemanager/{application id}.{service name}
        self.logger = qi.Logger(self.service_name)

        # Do some initializations before the service is registered to NAOqi
        self.logger.info("Initializing...")
        self.connect_services()
        self.logger.info("Initialized!")

        self.exp_folder_url = "/home/nao/.local/share/Explorer/"

    @qi.nobind
    def start_service(self):
        self.logger.info("Starting service...")
        # do something when the service starts
        self.logger.info("Started!")

    @qi.nobind
    def stop_service(self):
        # probably useless, unless one method needs to stop the service from inside.
        # external naoqi scripts should use ALServiceManager.stopService if they need to stop it.
        self.logger.info("Stopping service...")
        self.application.stop()
        self.logger.info("Stopped!")

    @qi.nobind
    def connect_services(self):
        # connect all services required by your module
        # done in async way over 30s,
        # so it works even if other services are not yet ready when you start your module
        # this is required when the service is autorun as it may start before other modules...
        self.logger.info('Connecting services...')
        self.services_connected = qi.Promise()
        services_connected_fut = self.services_connected.future()

        def get_services():
            try:
                self.memory = self.session.service('ALMemory')
                # connect other services if needed...
                self.logger.info('All services are now connected')
                self.services_connected.setValue(True)
            except RuntimeError as e:
                self.logger.warning('Still missing some service:\n {}'.format(e))

        get_services_task = qi.PeriodicTask()
        get_services_task.setCallback(get_services)
        get_services_task.setUsPeriod(int(2*1000000))  # check every 2s
        get_services_task.start(True)
        try:
            services_connected_fut.value(30*1000)  # timeout = 30s
            get_services_task.stop()
        except RuntimeError:
            get_services_task.stop()
            self.logger.error('Failed to reach all services after 30 seconds')
            raise RuntimeError


    ### Utility functions ###

    def showMaps(self):
        return os.listdir(self.exp_folder_url)

    def getMap(self,name):
        try:
            file = open(self.exp_folder_url+name, "r")
            return file.read()
        except:
            return None

    def uploadMap(self, content , name):
        if not name.endswith(".explo"):
            name = name + ".explo"

        with open( self.exp_folder_url+name , "w") as text_file:
            text_file.write( content )

        return True

    ### ################# ###

    def cleanup(self):
        # called when your module is stopped
        self.logger.info("Cleaning...")
        # do something
        self.logger.info("End!")

if __name__ == "__main__":
    # with this you can run the script for tests on remote robots
    # run : python my_super_service.py --qi-url 123.123.123.123
    app = qi.Application(sys.argv)
    app.start()
    service_instance = DecosNavigationFiles(app)
    service_id = app.session.registerService(service_instance.service_name, service_instance)
    service_instance.start_service()
    app.run()
    service_instance.cleanup()
    app.session.unregisterService(service_id)
