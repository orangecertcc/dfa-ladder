CC      = gcc
CFLAGS  = -Wall -Wextra -O3
LDFLAGS = 

all: ladderjac laddercoz

ladderjac:
	$(CC) $(CFLAGS) ladderjac.c x86_64_nistz.s common.c -o ladderjac

laddercoz:
	$(CC) $(CFLAGS) laddercoz.c x86_64_nistz.s common.c -o laddercoz

.PHONY: clean

clean:
	rm -rf ladderjac laddercoz
