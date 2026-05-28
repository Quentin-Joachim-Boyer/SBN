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

btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil).
% btree(btree(nil,nil,1,nil),btree(nil,nil,1,nil),2,nil).
%btree(btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),3,nil).
% btree(nil,nil,2,nil).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Génération des déclaration de noeuds de contrôle sous contexte O
control_node(D0,O0)         :- btree(btree(T11,T12,D1,_),btree(T21,T22,D2,_),D0,O0).
btree(T11,T12,D1,O0)        :- btree(btree(T11,T12,D1,_),btree(T21,T22,D2,_),D0,O0).
btree(T21,T22,D2,c(D0,O0))  :- btree(btree(T11,T12,D1,_),btree(T21,T22,D2,_),D0,O0).

% Declaration des noeuds sous contexte O et de l'espace des états associé.
node(1..D,O) :- btree(_,_,D,O).
state(0..2**D-1,O) :- btree(_,_,D,O).

% Declaration du domaine des poids sous contexte O.
&dom{(-D)..D} = w(I,J,O) :- node(I,O), node(J,O), D = #max {Dd:btree(_,_,Dd,O)}. % Borne potentiellement à changer.

% Déballage de la chaîne des noeuds de contrôle activé dans le contexte O.
offset_node(N,C,c(N,C)) :- btree(_,_,_,c(N,C)).
offset_node(N,C,O) :- offset_node(_,c(N,C),O).

% Contrainte assurant que le noeud CN soit bien un noeud de contrôle sous le contexte O (Cf rapport Danwen)
w(I,CN,nil) = 0 :- control_node(CN,O),node(I,O), I < CN.
&sum{ w(ON,CN,nil): offset_node(ON,_,O);w(CN,CN,nil)} = 1 :- control_node(CN,O).

% &sum{w(ON,CN,nil) : offset_node(ON,_,O)} >= w(I,CN,nil):- control_node(CN,O),node(I,O), I < CN.
% &sum{w(I,CN,nil): node(I,O); w(CN,CN,nil); -1*w(ON,CN,nil): offset_node(ON,_,O)} > 0 :- control_node(CN,O).

% Contrainte assurant que la dynamique du SBN sous contexte O correspondent bien à celle du réseau principal (de contexte nil).
&sum{w(NI,N,O) : node(NI,O), activated(NI,S,O)} >  0 :- transition_function_bit(N,S,O).
&sum{w(NI,N,O) : node(NI,O), activated(NI,S,O)} <= 0 :- not transition_function_bit(N,S,O), node(N,O), state(S,O).

% Génération des labels d'activation des états.
activated(N,S,O) :- node(N,O), state(S,O), (S / 2**(N-1)) \ 2 = 1.

% Génération des fonctions des bits des transition sous contexte O.
transition_function_bit(N,S,O) :- node(N,O), state(S,O),
    &sum{w(NI,N,nil) : node(NI,O), activated(NI,S,O); w(ON,N,nil):offset_node(ON,_,O)} > 0.

% Pour les fonctions de transition du reseau principal, génération de son encodage binaire.
transition_function(N,X) :- node(N,nil), X = #sum {2**S : state(S,nil),transition_function_bit(N,S,nil)}.

% Instruction d'affichage (à modifier uniquement pour le débug)
#show transition_function/2.
&show{w/3}.
#show offset_node/3.
% #show control_node/2.
% #show btree/4.
 #show node/2.
% #show state/2.