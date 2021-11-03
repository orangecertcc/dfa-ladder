set pagination off
set logging file gdb2.log
set logging on
b main
r
# breakpoint after pbit <- pbit XOR k_i
b *0xb6e6820c
disable 2
kill

set $ctr=0
while($ctr<40)
  r privkey.pem message.txt sig2.bin
  # do nothing for the first 238 ladder steps
  enable 2
  ignore 2 238
  c
  info registers
  # simulate random fault in register r6 (value of pbit for swaps)
  set $r6=0x55adab
  disable 2
  c
  set $ctr=$ctr+1
end
set logging off
quit
