set pagination off
set logging file gdb1.log
set logging on
b main
r
# breakpoint before pbit <- pbit XOR k_i
b *0xb6e68208
disable 2
kill

set $ctr=0
while($ctr<40)
  r privkey.pem message.txt sig1.bin
  # do nothing for the first 238 ladder steps
  enable 2
  ignore 2 238
  c
  info registers
  # skip instruction with a jump to the next one
  jump *0xb6e6820c
  disable 2
  c
  set $ctr=$ctr+1
end
set logging off
quit
