from multiprocessing import Process, Pipe

# define component
def add(a, b, sum):
    sum.send(a.recv()+b.recv())
    for conn in [a, b, sum]:
        conn.close()

# wire-up connection(s)
# --inputs for 'add'
net_in_a, add_in_a = Pipe()
net_in_b, add_in_b = Pipe()
# --inputs for 'add2'
net_in_c, add2_in_a = Pipe()
net_in_d, add2_in_b = Pipe()
# --inputs for 'add3'
add_out_sum, add3_in_a = Pipe()
add2_out_sum, add3_in_b = Pipe()
# --output for 'add3'
add3_out_sum, net_out_sum = Pipe()

# create process instance(s)
comp_add  = Process(target=add, args=(add_in_a, add_in_b, add_out_sum))
comp_add2 = Process(target=add, args=(add2_in_a, add2_in_b, add2_out_sum))
comp_add3 = Process(target=add, args=(add3_in_a, add3_in_b, add3_out_sum))

# run network
for comp in [comp_add, comp_add2, comp_add3]:
    comp.start()

# stimulate network with iip(s)
net_in_a.send(1)
net_in_b.send(2)
net_in_c.send(3)
net_in_d.send(4)
for conn in [net_in_a, net_in_b, net_in_c, net_in_d]:
    conn.close()

# wait for results
print net_out_sum.recv()
net_out_sum.close()

# terminate children before parent exits
for comp in [comp_add, comp_add2, comp_add3]:
    comp.join()
