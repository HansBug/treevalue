# distutils:language=c++
# cython:language_level=3

from libcpp cimport bool

cdef tuple _dict_flatten(object d)
cdef object _dict_unflatten(list values, tuple spec)

cdef tuple _list_and_tuple_flatten(object l)
cdef object _list_and_tuple_unflatten(list values, object spec)

cdef tuple _namedtuple_flatten(object l)
cdef object _namedtuple_unflatten(list values, object spec)

cdef tuple _dataclass_flatten(object l)
cdef object _dataclass_unflatten(list values, tuple spec)

cdef tuple _treevalue_flatten(object l)
cdef object _treevalue_unflatten(list values, tuple spec)

cdef bool _is_namedtuple_instance(pytree) except*

cpdef void register_integrate_container(object type_, object flatten_func, object unflatten_func) except*

cpdef object generic_flatten(object v)
cpdef object generic_unflatten(object v, tuple gspec)
