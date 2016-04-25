title: "The Autonomous Dumbledore"
published_on: April 25, 2016
author: Evy Kassirer
team: Web Frontend
...

When I arrived at Khan Academy to start my internship on the `Official SAT Practice <https://www.khanacademy.org/sat>`_ team, they had just released a huge new feature in the product: students could now link their PSAT scores to their Khan Academy accounts to immediately personalize their practice suggestions. This feature was very important to us, and everyone was proud of Khan Academy and College Board for completing it with such limited time.


The Problem
===========

Unfortunately, due to scheduled system maintenance periods, this feature occasionally has to be disabled. There were also a few bugs that surfaced over the week after the release, breaking the feature at unscheduled times. This forced folks from both Khan Academy and College Board to wake up in the middle of the night to check the status of PSAT linking and enable/disable the feature.

.. image:: /images/auto-dumble/sign-into-cb.png
    :alt: The prompt to sign into CollegeBoard.
    :class: align-center
    :height: 300px

.. class:: caption

    Our site when PSAT linking is enabled


.. image:: /images/auto-dumble/cb-maintenance.png
    :alt: Notice of CollegeBoard maintenance.
    :class: align-center
    :height: 150px

.. class:: caption

        Our site when PSAT linking is disabled


At Khan Academy, employee wellness is one of our top priorities. We were losing sleep over something that could be replaced with some code.


Introducing the Autonomous Dumbledore
=====================================

.. image:: /images/auto-dumble/robot-wizard.png
    :alt: A robot wizard
    :class: align-center
    :height: 400px

.. class:: caption

        Artist: `kcgreenn <http://midnitesurprise.com/post/11104265713/robot-wizard>`_


We decided to create the Autonomous Dumbledore, a friendly wizard that automagically updates Khan Academy’s site to reflect if PSAT linking is currently working. Here’s an overview of how Dumbledore works:

- `cron jobs <https://cloud.google.com/appengine/docs/python/config/cron>`_ are periodically running **endpoint tests**: we try to fetch PSAT scores from the College Board API endpoints, and record whether we succeeded or failed.

- another cron job looks at recent results of our endpoint tests - if enough of them succeeded or failed, we'll enable or disable the PSAT feature accordingly

However, deciding if the PSAT feature should be enabled or disabled was far from black and white. My mentor `John Sullivan <https://github.com/brownhead>`_ and I got thinking about how Dumbledore would decide the logic behind the magic.


When Should We Flip the Switch?
===============================

To decide to turn on and off the PSAT feature, we look at “**recent** results of our endpoint tests and see if **enough** tests are failing or passing to **enable or disable** the PSAT feature”.
But how recent? How many failing or passing tests are enough? Do those answers change when we enable vs. disable the feature?

Recent
------

Looking at recent test results is important to catch the endpoint going down soon after it happens. The further back we look, the more passing tests we’re looking at, and the harder it is to tell that things are mostly failing right now when looking at simple aggregate values like “ratio of successful tests to failed ones”. However, we are only able to do a few tests per minute. If we only look at the tests from the past minute, there won’t be enough data to make an educated decision.

Enough
------

How many tests should be passing to keep on the PSAT feature?
If we turn it off for any failure, any little error could turn off the PSAT feature for all of our users. If we only turned off the feature once every recent test was failing, bugs that only affected only some (but still many) users could break the feature in confusing ways for a lot of people and for a long time.

Right now we look at the past 5 minutes worth of endpoints tests and turn off the feature if less than 10% of the tests are passing. This means that the PSAT feature might not be working for up to 5 minutes before the site reflects it.

.. image:: /images/auto-dumble/slack-message-linking-disabled.png
    :alt: Slack message for linking disabled
    :class: align-center

.. class:: caption

        The message that `alertlib <https://github.com/Khan/alertlib>`_ sends us in Slack when PSAT linking turned off


Enabling vs. Disabling
----------------------

We then realized that deciding not to disable the feature was not the same as deciding to enable the feature. I mentioned above that we disable the feature if less than 10% of tests in the last 5 minutes are passing. If 50% of the tests in the last 5 minutes are passing, we wouldn’t decide to turn off PSAT linking, but if the feature was already off it doesn’t make sense to turn it back on yet, even though 50% isn’t less than 10%- 50% of tests are still failing! For the decision to turn the feature back on, we look at a longer timeframe of test results, and expect at least 90% of them to be passing.


.. image:: /images/auto-dumble/slack-message-linking-enabled.png
    :alt: Slack message for linking enabled
    :class: align-center

.. class:: caption

        The message that `alertlib <https://github.com/Khan/alertlib>`_ sends us in Slack when PSAT linking turned on

All of this logic got pretty complicated - there were even more subtleties than these! We carefully thought about how to clearly organize our code and unit test each piece of functionality to make sure Dumbledore was working as expected.

Google App Engine, Cron, and Deploy Fun
=======================================

After a few weeks of work, Dumbledore was ready! It was time to deploy him to the world to perform his magical duties. This took a bit longer than John and I were expecting, but we learned a bunch about Google App Engine and Cron in the process! Here are some highlights:

Composite indexes take a long time to build
-------------------------------------------

There are multiple College Board endpoints that we test. We store them in a class that looks like this:

.. code-block:: python

    class CollegeBoardTestResult(ndb.Model):
        """The results from a single test on College Board's servers.

        This serves as a record for whether College Board was up at this time.
        """

        # The type of test this entity stores the results for
        test_type = ndb.StringProperty(indexed=True, required=True,
                                       choices=["session-test", "oauth-test"])

        # Naive datetime (ie: tzinfo is None) recording when the test ended. Always
        # uses UTC time.
        end_time = ndb.DateTimeProperty(indexed=True, required=True,
                                        auto_now_add=True)

        # The actual results of the test, recording whether it was a success,
        # failure, partial success, partial failure, etc. The shape of this data
        # depends on the test type.
        data = object_property_ndb.JsonProperty(indexed=False, required=True)

        @classmethod
        def get_most_recent(cls, session_from_datetime, oauth_from_datetime):
            """Get all the results after the given datetimes."""
            return cls.query(
                ndb.OR(
                    ndb.AND(
                        cls.test_type == "session-test",
                        cls.end_time > session_from_datetime),
                    ndb.AND(
                        cls.test_type == "oauth-test",
                        cls.end_time > oauth_from_datetime)),
                ancestor=AutonomousDumbledoreStatus.get_singleton_key())

Note that when we fetch recent test results, we’re searching for test results of (1) a certain test_type and (2) a certain range of end_time. To make this lookup efficient, App Engine creates (when we deploy) a new `composite index <https://cloud.google.com/appengine/docs/python/datastore/entities#Python_Understanding_write_costs>`_ that refers to both :code:`test_type` and :code:`end_time`.

Turns out that creating this new composite index makes the deploy take several hours! Dumbledore would not work until we finished building the composite index, which prevented us from quickly seeing how Dumbledore performed in production and ended up pushing us past the deadline we set for the project. Now that we know deploying composite indexes takes a while, we can plan these deploys more strategically. I’ve also recently learned that it’s possible to create new indexes *outside of deploys* with :code:`gcloud preview app deploy index.yaml`, which takes equally as long but can be started before the rest of the change is ready to deploy.

Cron isn’t built to run continuously
-------------------------------------

Remember when I said we have cron jobs running all the time to collect information about the College Board endpoints? Turns out App Engine’s cron doesn’t like running tasks back to back.

This is how we got it to work:

1. We set the timing in the `cron configuration file <https://cloud.google.com/appengine/docs/python/config/cron>`_ to be schedule: :code:`every 1 minutes synchronized`. The minimum amount of time we can wait between cron jobs is 1 minute. By default, :code:`every 1 minutes` would start a new task one minute after the previous ended. Adding :code:`synchronized` has it run every minute.

2. Stop the handler servicing cron’s request after 45 seconds. When we let it run for the full minute, it would take some time to wrap up, go over a minute, and stop the job synchronously scheduled for the next minute from starting. When we stopped it after 45 seconds, which is a pretty hacky way to solve our problem, the job was always able to start at the beginning of every minute.

For various reasons, we couldn’t properly test this without actually uploading the code to App Engine. It took around 10 deploys to figure out how to get it working in production, but finally the Autonomous Dumbledore was alive and working well!

The Awesome Results of the Autonomous Dumbledore
=================================================

- If outages start late or end earlier than planned, we can detect it and keep the PSAT feature up, allowing students to use it for (almost) the full time the system is up
- Sometimes outages last a bit longer than expected, and that’s automatically handled
- We learned a bunch of cool stuff about Google App Engine and Cron

And my favourite...

- No one has to stay up late or wake up early to monitor logs and flip a switch!
