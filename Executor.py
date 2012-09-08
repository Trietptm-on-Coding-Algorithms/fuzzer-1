from winappdbg import Debug, win32
from MyEventHandler import MyEventHandler
import logging
from sys import stdout 
from time import time

def executor(cmd_line, offset, value_index, new_file, run_number, save_directory, child_conn, timeout=5):
    ''' Setup the debugger and the event handler. Execute the process, and after completion log the
        run-specific information, as well as check for any specific output generated by the event handler. '''
    
    # create a new process, run it
    handler = MyEventHandler(new_file, save_directory)   
    try:
        debug   = Debug(handler, bKillOnExit=True)
        process = debug.execl(cmd_line)

        max_time = time() + timeout
        while debug and time() < max_time:
            try:
                debug.wait(500)   # 500 milliseconds accuracy

            # If wait() times out just try again. On any other error stop debugging.
            except WindowsError, e:
                if e.winerror in (win32.ERROR_SEM_TIMEOUT, win32.WAIT_TIMEOUT):
                    continue
                raise

            # Dispatch the event and continue execution.
            try:
                debug.dispatch()
            finally:
                debug.cont()
            
    finally:
        debug.stop()

    # after completion, log the run
    output = '%s %d %s\n' % ('-'*10, run_number, '-'*10)
    output += 'Running : %s\n' % cmd_line
    output += 'run number = %d, offset = %d, value_index = %d\n' % (run_number, offset, value_index)   

    # if any signals are handled, debug output will be non-empty
    handler_output = handler.getOutput()
    if handler_output:
        output += 'handler_output = \n%s\n' % handler_output          #### HAVE THIS GENERATE A HIGHER LOG LEVEL
        print '\n'+'-'*20
        print '[!] Crash! Run number %d' % run_number
        print output
        print '\n'+'-'*20

    child_conn.send_bytes(output)
    child_conn.close()