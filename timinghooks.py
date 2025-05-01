"""
A class to support placement of timing points in a Python application.
"""
import time
import threading
import contextlib
import numpy


class Timers:
    """
    Manage multiple named timers. See interval() method for example
    usage. The reportFromTemplate() method can be used to generate
    a formatted report on the timings.

    Maintains a dictionary of pairs of start/finish times, before and
    after particular operations. These are grouped by operation names,
    and for each name, a list is accumulated of the pairs, for every
    time when this operation was carried out.

    Timing intervals can be safely nested, so some intervals can be
    contained with others.

    The object is thread-safe, so multiple threads can accumulate to
    the same names. The object is also pickle-able.

    Example Usage::

        timings = Timers()
        with timings.interval('walltime'):
            for i in range(count):
                # Some code with no specific timer

                with timings.interval('reading'):
                    # Code to do reading operations

                with timings.interval('computation'):
                    # Code to do computation

        template = '\n'.join([
            "Walltime:    {walltime@total:.2f}",
            "Reading:     {reading@total:.2f}",
            "Computation: {computation@total:.2f}"
        ])
        reportStr = timings.reportFromTemplate(template)
        print(reportStr)

    This would report the total time spent within each of the named interval
    code blocks.

    These 'with interval' blocks can be scattered through an application's
    code, all using the same timings object. The report can be generated
    at the end of the application to present to a user, showing how the
    key parts of the application compare in time taken.

    """
    def __init__(self):
        self.pairs = {}
        self.lock = threading.Lock()

    @contextlib.contextmanager
    def interval(self, intervalName):
        """
        Use as a context manager to time a particular named interval.

        Example::

            timings = Timers()
            with timings.interval('some_action'):
                # Code block required to perform the action

        After exit from the `with` statement, the timings object will have
        accumulated the start and end times around the code block. These
        will then contribute to the reporting of time intervals.

        """
        startTime = time.time()
        yield
        endTime = time.time()
        with self.lock:
            if intervalName not in self.pairs:
                self.pairs[intervalName] = []
            self.pairs[intervalName].append((startTime, endTime))

    def getDurationsForName(self, intervalName):
        """
        For the given interval name, turns that list of start/end times
        into a list of durations (end - start), in seconds.

        Returns the list of durations.
        """
        if intervalName in self.pairs:
            intervals = [(p[1] - p[0]) for p in self.pairs[intervalName]]
        else:
            intervals = None
        return intervals

    def merge(self, other):
        """
        Merge another Timers object into this one
        """
        with self.lock:
            for intervalName in other.pairs:
                if intervalName in self.pairs:
                    self.pairs[intervalName].extend(other.pairs[intervalName])
                else:
                    self.pairs[intervalName] = other.pairs[intervalName]

    def makeSummaryDict(self):
        """
        Make some summary statistics, and return them in a dictionary
        """
        d = {}
        for name in self.pairs:
            intervals = numpy.array(self.getDurationsForName(name))
            tot = intervals.sum()
            minVal = intervals.min()
            maxVal = intervals.max()
            meanVal = intervals.mean()
            pcnt25 = numpy.percentile(intervals, 25)
            pcnt50 = numpy.percentile(intervals, 50)
            pcnt75 = numpy.percentile(intervals, 75)
            d[name] = {'total': tot, 'min': minVal, 'max': maxVal,
                'lowerq': pcnt25, 'median': pcnt50, 'upperq': pcnt75,
                'mean': meanVal, 'count': len(intervals)}
        return d

    def reportFromTemplate(self, templateStr):
        """
        Given a template string, produce a formatted report on timings

        The template string should be a Python format template. The
        format() method on this string will be called, given a dictionary
        of field names. The available field names are created from
        the timer names and the summary statistic names.

        All field names are of the form <timer name>@<statistic name>.
        The available statistics are total, min, max, mean, median,
        upperq, count.

        For example, if the user has given a timing interval named "reading",
        then the available field names will include "reading@total",
        "reading@min", etc.

        The most commonly used statistic will often be "total", but the
        others are available if required.

        Returns the formatted report as a single string.
        """
        summary = self.makeSummaryDict()
        fieldDict = {}
        for intervalName in summary:
            for stat in summary[intervalName]:
                fieldName = "{}@{}".format(intervalName, stat)
                fieldDict[fieldName] = summary[intervalName][stat]
        report = templateStr.format(**fieldDict)
        return report

    def __getstate__(self):
        """
        Ensure pickleability by omitting the lock attribute
        """
        d = {}
        with self.lock:
            d.update(self.__dict__)
        d.pop('lock')
        return d

    def __setstate__(self, state):
        """
        For unpickling, add a new lock attribute
        """
        self.lock = threading.Lock()
        with self.lock:
            self.__dict__.update(state)


def tests():
    """
    Run some tests
    """
    
