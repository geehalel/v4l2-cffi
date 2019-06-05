#ifndef _LINUX_IOCTL_H
#define _LINUX_IOCTL_H

/* #include <asm/ioctl.h> */

/* cffi: /usr/include/sys/ioctl.h */
/* Perform the I/O control operation specified by REQUEST on FD.
   One argument may follow; its presence and type depend on REQUEST.
   Return value depends on REQUEST.  Usually -1 indicates error.  */
extern int ioctl (int __fd, unsigned long int __request, ...);

#endif /* _LINUX_IOCTL_H */
