# Host build + unit tests for the portable tag firmware.
# On target, compile src/*.c with the vendor SDK (PHY6222 / Telink) plus a hal_<soc>.c.
CC ?= gcc
CFLAGS ?= -std=c99 -O2 -Wall -Wextra -DCH_HOST_TEST -D_DEFAULT_SOURCE
SRC = src/app.c src/motion.c src/ntc.c src/payload.c test/hal_sim.c test/test_main.c

test: build/test_tag
	./build/test_tag

build/test_tag: $(SRC) src/*.h test/*.h
	mkdir -p build
	$(CC) $(CFLAGS) $(SRC) -lm -o $@

clean:
	rm -rf build
.PHONY: test clean
