from mwr.common import cli

from drozer.payload import builder, manifest

class PayloadManager(cli.Base):
    """
    drozer payload COMMAND [OPTIONS]
    
    A utility for building custom drozer Agents to use as payloads.
    """
    
    def __init__(self):
        cli.Base.__init__(self)
        
        self._parser.add_argument("--no-gui", action="store_true", default=False, help="create an agent with no GUI")
        self._parser.add_argument("--permission", "-p", nargs="+", help="add a permission to the Agent manifest")
        self._parser.add_argument("--server", default=None, metavar="HOST[:PORT]", help="specify the address and port of the drozer server")
        
    def do_build(self, arguments):
        """build a drozer Agent"""
        
        source = arguments.no_gui and "guiless-agent" or "gui-agent"
        print source
        packager = builder.Packager()
        packager.copy_sources_from(source)
        
        if arguments.no_gui:
            e = manifest.Endpoint(packager.endpoint_path())
            if arguments.server != None:
                e.put_server(arguments.server)
            e.write()
        
        if arguments.permission != None:
            m = manifest.Manifest(packager.manifest_path())
            for p in arguments.permission:
                m.add_permission(p)
            m.write()
        
        built = packager.package()
        
        print "Done:", built