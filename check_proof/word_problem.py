"""
Using a HIKMOT-style certified solution to the gluing equations to
solve the word problem in a hyperbolic 3-manifold group.
"""

from snappy import Manifold
from snappy.snap.interval_reps import contains_one, could_be_equal, diameter
from snappy.snap.polished_reps import SL2C_inverse
from sage.all import gcd, ZZ

def pairs(xs):
    for i, x in enumerate(xs):
        for y in xs[i+1:]:
            yield (x, y)

def is_manifold(manifold):
    """
    >>> is_manifold(Manifold('m004(0,0)'))
    True
    >>> is_manifold(Manifold('m004(1,2)'))
    True
    >>> is_manifold(Manifold('m004(4,2)'))
    False
    >>> is_manifold(Manifold('m125(0,0)(1.3,4.5)'))
    False
    """
    for a, b in manifold.cusp_info('filling'):
        try:
            a, b = ZZ(a), ZZ(b)
            if a == 0 and b == 0:
                continue
            if gcd(a, b) != 1:
                return False
        except TypeError:
            return False
    return True

def jorgensens_inequality_fails(A, B):
    """
    Given two matrices A and B in GL(2, ComplexIntervalField), returns
    whether they provably *fail* Jorgensen's inequality. 

    It is assumed that each matrix contains an element of SL(2, C)
    which is actually the matrix of interest.  If the function returns
    True, then any Kleinian group generated by one SL(2, C) matrix in
    A and one SL(2, C) matrix in B is necessarily elementary.  

    >>> M = Manifold('m004')
    >>> _, rho = M.verify_hyperbolicity(holonomy=True)
    >>> A, B, I = rho('a'), rho('b'), rho('')
    >>> jorgensens_inequality_fails(A, B)
    False
    >>> jorgensens_inequality_fails(I, B)
    True
    >>> jorgensens_inequality_fails(B, I)
    True
    >>> R = rho(rho.relators()[0])
    >>> jorgensens_inequality_fails(R, I)
    True
    >>> jorgensens_inequality_fails(A, R)
    True
    >>> jorgensens_inequality_fails(A, A)
    False

    Note that Jorgensen's inequality is not symmetric in A and B, so
    we actually apply both tests, and return True if either of them
    provably fails.
    """
    def trace(x):
        return x.trace()
    Ainv = SL2C_inverse(A)
    Binv = SL2C_inverse(B)
    assert contains_one(A*Ainv) and contains_one(B*Binv)
    first_term = min(abs(trace(A)**2 - 4), abs(trace(B)**2 - 4))
    mu = first_term + abs(trace(A*B*Ainv*Binv) - 2)
    return mu < 1


class WordProblemSolver(object):
    """
    Solves the word problem for a hyperbolic manifold where we can
    rigorously verify the existence of the hyperbolic structure. 

    >>> M = Manifold('s612(3,4)')
    >>> wps = WordProblemSolver(M, bits_prec=60)
    >>> wps.is_nontrivial('aab')
    True
    >>> wps.is_trivial('aab')
    False
    >>> all(wps.is_nontrivial(g) for g in wps.rho.generators())
    True
    >>> all(wps.is_trivial(R) for R in wps.rho.relators())
    True

    We can run into precision issues; in this case the image of R^3 is
    so smeared out we can't tell that it's the identity.

    >>> R = wps.rho.relators()[-1]
    >>> wps.is_trivial(3*R)
    Traceback (most recent call last):
        ...
    ValueError: Failed to solve the word problem at this precision.
    >>> wps.rho(3*R)[0,0].diameter()  # doctest: +ELLIPSIS
    1.899905...
    >>> wps = WordProblemSolver(M, bits_prec=100)
    >>> wps.is_trivial(3*R)
    True
    """
    def __init__(self, manifold, bits_prec=100, fundamental_group_args=[True, True, False]):
        if not is_manifold(manifold):
            raise ValueError('Sorry, we do not support orbifold singularities')
        
        success, rho = manifold.verify_hyperbolicity(bits_prec=bits_prec, holonomy=True,
                                                     fundamental_group_args=fundamental_group_args,
                                                     lift_to_SL = True)
        if not success:
            raise ValueError("Could not verify the holonomy representation.")

        self.rho = rho
        self._find_noncommuting_gens()

    def _find_noncommuting_gens(self):
        rho = self.rho
        for g, h in pairs(rho.generators()):
            if not contains_one(rho(g + h + (g + h).upper())):
                self.noncommmuting_gens = (g, h)
                self.noncommmuting_mats = rho(g), rho(h)
                return
        raise ValueError("Could not verify a pair of noncommuting gens.")

    def is_nontrivial(self, word):
        X = self.rho(word)
        if not contains_one(X):
            return True
        # Should be trivial, but we need to prove this. The point is
        # we know that A, B, and X contain elements of a torision-free
        # Kleinian group.  If <A, X> and <B, X> are both elementary
        # but <A, B> is not, it follows that X must be the identity.
        A, B = self.noncommmuting_mats
        if jorgensens_inequality_fails(X, A) and jorgensens_inequality_fails(X, B):
            return False
        raise ValueError('Failed to solve the word problem at this precision.')
        
    def is_trivial(self, word):
        return not self.is_nontrivial(word)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    M = Manifold('s612(3,4)')
    wps = WordProblemSolver(M, bits_prec=60)
