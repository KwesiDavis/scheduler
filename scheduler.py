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
# --output for 'add'
add_out_sum, net_out_sum = Pipe()

# create process instance
comp_add = Process(target=add, args=(add_in_a, add_in_b, add_out_sum))

# stimulate network with iip(s)
net_in_a.send(3)
net_in_b.send(5)
for conn in [net_in_a, net_in_b]:
    conn.close()

# run network
comp_add.start()

# wait for results
print net_out_sum.recv()
net_out_sum.close()

# terminate child before parent exits
comp_add.join()
