% Ejemplo completo sin errores lexicos
padre(juan, ana).
padre(juan, pedro).

/* Regla que utiliza variables */
abuelo(X, Z) :-
    padre(X, Y),
    padre(Y, Z).

?- abuelo(juan, Quien).

datos('Juan Perez', "cadena con espacios", 25, 3.14, _Temporal, _).
calculo(Resultado) :- Resultado is 10 + 2 * 3 - 4 / 2 // 1 ** 2 mod 3.
comparar(X, Y) :- X = Y; X \= Y, X == X, X \== Y, X =.. [dato, X].
orden(X, Y) :- X < Y, X =< Y, Y > X, Y >= X.
control(X) :- \+ falso(X), !.
lista([a, b | Resto]) :- Resto = [c].
estructura({dato}).
regla --> [a, b].
