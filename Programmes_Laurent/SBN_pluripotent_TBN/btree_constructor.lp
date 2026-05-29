%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% INPUT : .

% OUTPUT clingcon : Dynamiques (projection sur les fonctions de transition) 
%   de SBNs de poids bornés vérifiant un arbre de decomposition donné.
% 
% OUTPUT Approxasp : Leur nombre

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% PARAMETRES :

% Declaration d'un arbre de decomposition pour lancer ce programme seul.
% Il est recommandé d'utiliser les fichier setup_btree{d}d.lp pour une utilisation systématique.

% btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil).
% btree(btree(nil,nil,1,nil),btree(nil,nil,1,nil),2,nil).
btree(btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),3,nil).
% btree(nil,nil,2,nil).
% btree(btree(btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),3,nil),btree(btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),3,nil),4,nil).
% btree(btree(nil,nil,3,nil),btree(btree(nil,nil,2,nil),btree(btree(nil,nil,1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),3,nil),4,nil).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Dimension de Travail.
d(D) :- D = #max {Dd:btree(_,_,Dd,_)}.

% Déballage de l'arbre de décomposition.
btree(T11,T12,D1,O0)        :- btree(btree(T11,T12,D1,_),btree(_,_,_,_),_,O0).
btree(T21,T22,D2,c(D0,O0))  :- btree(btree(_,_,_,_),btree(T21,T22,D2,_),D0,O0).
context(D,O)  :- btree(_,_,D,O).


% Déclaration des noeuds de contrôle sous contexte C.
control_node(D0,O0)         :- btree(btree(_,_,_,_),btree(_,_,_,_),D0,O0).


% % Declaration des noeuds et de l'espace des états associé.
node(1..D) :- d(D).
state(0..2**D-1) :- d(D).

% % Declaration des noeuds des sous réseaux. 
% node(1..CN-1,c(CN,O)) :- control_node(CN,O).
% node(1..CN-1,O) :- control_node(CN,O).

% % Declaration du domaine des poids.
% &dom{-D..D} = w(I,J) :- node(I),node(J),d(D).

% Declaration du domaine des poids des sous réseaux.
&dom{(-D)..D} = w(I,J,context(D,O)) :- node(I), node(J), context(D,O), I <= D, J <= D. % Borne potentiellement à changer.

% Projection des noeuds du réseau principal.
% &dom{(-D)..D} = w(I,J) :- node(I), node(J), d(D).
% &sum{w(I,J); -1*w(I,J,context(D,nil))} = 0 :- node(I), node(J), d(D).  


% Déballage de la chaîne des noeuds de contrôle activés dans un contexte.
offset_node(N,C,c(N,C)) :- context(_,c(N,C)).
offset_node(N,C,O) :- offset_node(_,c(N,C),O).

% % Contrainte assurant que le noeud CN soit bien un noeud de contrôle sous le contexte O (Cf rapport Danwen)
% w(I,CN,nil) = 0 :- control_node(CN,O),node(I), I < CN.
% &sum{ w(ON,CN,nil): offset_node(ON,_,O);w(CN,CN,nil)} = 1 :- control_node(CN,O).

% Contrainte de non activation externe.
&sum{w(ON,CN,context(D,nil)) : offset_node(ON,_,O) ; pos_w(I,CN) : node(I), I < CN} <= 0 :- control_node(CN,O), d(D).
% Variables auxiliaires.
&dom{0..D} = pos_w(I,J) :- node(I),control_node(J,_), d(D),I < J.
&sum{pos_w(I,J) ; -1*w(I,J,context(D,nil))} >= 0 :- node(I),control_node(J,_), d(D),I < J.

% Contrainte de non désactivation externe.
&sum{w(ON,CN,context(D,nil)) : offset_node(ON,_,O) ; neg_w(I,CN) : node(I), I < CN ; w(CN,CN,context(D,nil))} > 0 :- control_node(CN,O), d(D).
% Variables auxiliaires.
&dom{-(D)..0} = neg_w(I,J) :- node(I),control_node(J,_), d(D), I < J.
&sum{neg_w(I,J) ; -1*w(I,J,context(D,nil))} <= 0 :- node(I),control_node(J,_), d(D),I < J.


% Contraintes assurant que la dynamique du sous réseau sous contexte 
% correspondent bien à celle d'un SBN (avec d'autres poids, mais de seuil 0).
&sum{w(NI,N,context(D,O)) : node(NI), activated(NI,S), NI <= D} >  0 :- 
    transition_function_bit(N,S,context(D,O)).
&sum{w(NI,N,context(D,O)) : node(NI), activated(NI,S), NI <= D} <= 0 :- 
    -transition_function_bit(N,S,context(D,O)).%, node(N), state(S), context(D,O), N <= D.

% Déclaration de l'activation du noeud N dans l'état S.
activated(N,S) :- node(N), state(S), (S / 2**(N-1)) \ 2 = 1.
% Déclaration de l'activation du noeud N dans l'état S sous contexte.
% (Soit par nature de l'état, soit par forçage du contexte)
activated(N,S,context(D,O)) :- activated(N,S), context(D,O), N <= D.
activated(N,S,context(D,O)) :- node(N), state(S), offset_node(N,_,O), context(D,O).

% Génération des fonctions des bits des transition sous contexte.
transition_function_bit(N,S,context(D,O)) :- node(N), state(S), context(D,O), N <= D,
    &sum{w(NI,N,context(Dd,nil)) : node(NI), activated(NI,S,context(D,O)),d(Dd)} > 0.
-transition_function_bit(N,S,context(D,O)) :- node(N), state(S), context(D,O), N <= D,
    &sum{w(NI,N,context(Dd,nil)) : node(NI), activated(NI,S,context(D,O)),d(Dd)} <= 0.

% Pour les fonctions de transition du reseau principal, génération de son encodage binaire.
transition_function(N,X) :- node(N), d(D), 
    X = #sum {2**S : state(S),transition_function_bit(N,S,context(D,nil))}.

% % Instruction d'affichage (à modifier uniquement pour le débug)
#show transition_function/2.
&show{w/3}.
% #show transition_function_bit/3.
% #show offset_node/3.
% #show control_node/2.
% #show context/2.
% #show btree/4.
% #show node/2.
% #show state/1.
% #show activated/3.