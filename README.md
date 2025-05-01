# timinghooks
Support to set up custom timing hooks in Python applications. The main intention is to allow a programmer to embed timing points in key locations in an application, collecting identifiable timing data on sections of code, and produce summary statistics of the collected data. This will allow an application to report in simple terms on how the running time is distributed across different key parts of the code.

The timinghooks module provides the `Timers` class. An object of this class will manage multiple named timers. The general idea is to have one of these for the whole application, and pass it around to any part of the code which needs timing.

The `makeSummaryDict()` method can be used to generate summary statistics on the timings.

Maintains a dictionary of pairs of start/finish times (in seconds), before and after particular operations. These are grouped by operation names, and for each name, a list is accumulated of the pairs, for every time when this operation was carried out.

The operation names are arbitrary strings chosen by the user at each point where a timer is embedded in the application code.

Timing intervals can be safely nested, so some intervals can be contained with others.

The object is thread-safe, so multiple threads can accumulate to the same names. The object is also pickle-able.

### Example Usage
```python
timings = Timers()
with timings.interval('walltime'):
    for i in range(count):
        # Some code with no specific timer

        with timings.interval('reading'):
            # Code to do reading operations

        with timings.interval('computation'):
            # Code to do computation

summary = timings.makeSummaryDict()
print(summary)
```

The resulting summary dictionary would be something like
```
{'walltime': ['total': 12.345, 'min': 1.234, ......],
 'reading': ['total': 3.456, 'min': 0.234, ......],
 'computation': ['total': 9.123, 'min': 1.012, ......]
}
```
In practice, one would select relevant entries in this summary dictionary to generate a human-readable report on timings. The `total` entry for each timer is usually the most interesting, the others give some idea of variability.

These "with interval" blocks can be scattered through an application's code, all using the same timings object. The summary dictionary can be used to generate a report at the end of the application to present to a user, showing how the key parts of the application compare in time taken.
