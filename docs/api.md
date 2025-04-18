# API Reference

```{eval-rst}
.. module:: stamina

.. autofunction:: retry
.. autofunction:: retry_context
.. autoclass:: Attempt
   :members: num, next_wait
.. autoclass:: RetryingCaller
   :members: on, __call__

   For example::

      def do_something_with_url(url, some_kw):
          resp = httpx.get(url).raise_for_status()
          ...

      rc = stamina.RetryingCaller(attempts=5)

      rc(httpx.HTTPError, do_something_with_url, f"https://httpbin.org/status/404", some_kw=42)

      # Equivalent:
      bound_rc = rc.on(httpx.HTTPError)

      bound_rc(do_something_with_url, f"https://httpbin.org/status/404", some_kw=42)

   Both calls to ``rc`` and ``bound_rc`` run

   .. code-block:: python

      do_something_with_url(f"https://httpbin.org/status/404", some_kw=42)

   and retry on ``httpx.HTTPError``.

.. autoclass:: BoundRetryingCaller
   :members: __call__

.. autoclass:: AsyncRetryingCaller
   :members: on, __call__

.. autoclass:: BoundAsyncRetryingCaller
   :members: __call__
```


## Activation and deactivation

```{eval-rst}
.. autofunction:: set_active
.. autofunction:: is_active
```

## Testing

::: {seealso}
{doc}`testing`
:::

```{eval-rst}
.. autofunction:: set_testing
.. autofunction:: is_testing
```

## Instrumentation

::: {seealso}
{doc}`instrumentation`
:::

```{eval-rst}
.. module:: stamina.instrumentation

.. autofunction:: set_on_retry_hooks
.. autofunction:: get_on_retry_hooks

.. autoclass:: RetryHook()

   For example::

      def print_hook(details: stamina.instrumentation.RetryDetails) -> None:
          print("a retry has been scheduled!", details)

      stamina.set_on_retry_hooks([print_hook])

.. autoclass:: RetryHookFactory

   For example, if your instrumentation needs to import a module ``something_expensive`` which takes a long time to import, you can delay it until the first retry (or call to :func:`stamina.instrumentation.get_on_retry_hooks`)::

      from stamina.instrumentation import RetryHookFactory, RetryDetails

       def init_with_expensive_import():
           import something_expensive

           def do_something(details: RetryDetails) -> None:
               something_expensive.do_something(details)

           return do_something


       stamina.set_on_retry_hooks([RetryHookFactory(init_with_expensive_import)])

.. autoclass:: RetryDetails
```

### Integrations

```{eval-rst}
.. data:: StructlogOnRetryHook

  Pass this object to :func:`stamina.instrumentation.set_on_retry_hooks` to activate *structlog* integration.

  Is active by default if *structlog* can be imported.

  .. seealso:: :ref:`structlog`

  .. versionadded:: 23.2.0

.. data:: LoggingOnRetryHook

   Pass this object to :func:`stamina.instrumentation.set_on_retry_hooks` to activate :mod:`logging` integration.

   Is active by default if *structlog* can **not** be imported.

   .. seealso:: :ref:`logging`

   .. versionadded:: 23.2.0

.. data:: PrometheusOnRetryHook

   Pass this object to :func:`stamina.instrumentation.set_on_retry_hooks` to activate Prometheus integration.

   Is active by default if *prometheus-client* can be imported.

   .. seealso:: :ref:`prometheus`

   .. versionadded:: 23.2.0
.. autofunction:: get_prometheus_counter
```
