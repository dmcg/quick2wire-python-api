
from contextlib import closing
import posix
from fcntl import ioctl
from quick2wire.i2c_ctypes import *
from ctypes import create_string_buffer, sizeof, c_int, byref, pointer, addressof, string_at


def read(addr, n_bytes):
    """An I2C I/O message that reads n_bytes bytes of data"""
    return read_into(addr, create_string_buffer(n_bytes))

def read_into(addr, buf):
    """An I2C I/O message that reads into an existing ctypes string buffer."""
    return _new_i2c_msg(addr, I2C_M_RD, buf)

def write_bytes(addr, *bytes):
    """An I2C I/O message that writes one or more bytes of data. 
    
    Each byte is passed as an argument to this function.
    """
    return write(addr, bytes)

def write(addr, byte_seq):
    """An I2C I/O message that writes one or more bytes of data.
    
    The bytes are passed to this function as a sequence.
    """
    buf = bytes(byte_seq)
    return _new_i2c_msg(addr, 0, create_string_buffer(buf, len(buf)))


def _new_i2c_msg(addr, flags, buf):
    return i2c_msg(addr=addr, flags=flags, len=sizeof(buf), buf=buf)


class I2CBus:
    """Performs I2C I/O transactions on one I2C bus.
    
    Transactions are performed by passing one or more I2C I/O messages
    to the transaction method of the bus.  I2C I/O messages are created
    with the read, read_into, write and write_bytes functions defined in
    the quick2wire.i2c module.
    
    An I2CBus acts as a context manager, allowing it to be used in a
    with statement.  The bus is closed at the end of the with statement.
    
    For example:
    
        import quick2wire.i2c as i2c
        
        with i2c.I2CBus() as bus:
            bus.transaction(
                i2c.write(0x20, bytes([0x01, 0xFF])))
    
    """
    
    def __init__(self, n=0, extra_open_flags=0):
        """Opens the bus device.
        
        Arguments:
        n                -- the number of the bus (default 0,
                            the bus on the Raspberry Pi accessible
                            via the header pins).
        extra_open_flags -- extra flags passed to posix.open when 
                            opening the I2C bus device file (default 0; 
                            e.g. no extra flags).
        """
        self.fd = posix.open("/dev/i2c-%i"%n, posix.O_RDWR|extra_open_flags)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    
    def close(self):
        """
        Closes the I2C bus device.
        """
        posix.close(self.fd)
    
    def transaction(self, *msgs):
        """
        Perform an I2C I/O transaction.

        Arguments:
        *msgs - I2C messages created by one of the read, read_into,
                write or write_bytes functions.
        """
        
        msg_count = len(msgs)
        msg_array = (i2c_msg*msg_count)(*msgs)
        ioctl_arg = i2c_rdwr_ioctl_data(msgs=msg_array, nmsgs=msg_count)
        
        ioctl(self.fd, I2C_RDWR, addressof(ioctl_arg))
        
        return [i2c_msg_to_bytes(m) for m in msgs if (m.flags & I2C_M_RD)]


def i2c_msg_to_bytes(m):
    return string_at(m.buf, m.len)

