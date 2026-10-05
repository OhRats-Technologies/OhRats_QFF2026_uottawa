OPENQASM 3.0;
include "stdgates.inc";
qubit[4] q;
ry(-0.4) q[0];
cx q[0], q[1];
cx q[0], q[2];
cx q[0], q[3];
x q[0];
x q[2];
