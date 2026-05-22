#const d = 3.
#const w_bound = d.
#const f0 = 0.
#const f1 = 0.
#const f2 = 0.

node(0..d-1).

state(0..2**d-1).

{w(N1,N2,V): V =(-w_bound)..w_bound} = 1 :- node(N1),node(N2).

#sum {2**N : activated(N,S) : node(N)} = S :- state(S).


transition_function_bit(N,S) :- node(N), state(S), #sum {V:w(NI,N,V),node(NI),activated(NI,S)} > 0.
transition_function(N,X) :- node(N), X = #sum {2**S : state(S),transition_function_bit(N,S)}.

:- not transition_function(0,f0).
:- not transition_function(1,f1).
:- not transition_function(2,f2).
 
#show.