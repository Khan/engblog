title: "The Original Serverless Architecture is Still Here"
published_on: May 31, 2018
author: Kevin Dangoor
team: Infrastructure
...

This month, my colleague Dave Rosile and I went to [GlueCon](http://gluecon.com) 2018 in sunny Denver, Colorado. The organizers did a fantastic job putting together a conference around modern server architectures.

In talking about those architectures, there were a bunch of talks related to container orchestration (which is now synonymous with [Kubernetes](https://kubernetes.io)), and [serverless approaches](https://martinfowler.com/articles/serverless.html).

## Kubernetes gives you flexibility

Kubernetes and the ecosystem around it strike me as something distinctly different from what we had in the decades before it. Starting with Docker containers as a common format for deploying complete and immutable images of software, Kubernetes layers on management of those containers to start and stop them as needed. Docker is still relatively low-level, describing only one container, so there’s [Helm](https://helm.sh) to help package up larger solutions. There are a few “ingress controllers” to manage traffic coming into a Kubernetes service, and a number of ways to monitor what’s going on within your Kubernetes clusters (for example, [Prometheus](https://prometheus.io) and [InfluxDB](https://www.influxdata.com/products/integrations/)). There’s even [Istio](https://istio.io) and other service mesh solutions to control how your services talk to one another. And none of this ties you to a single company’s cloud.

That ecosystem is powerful and flexible, enabling you to put together whatever collection of software you think is right for the job at hand. Flexibility doesn’t come free, though. In some cases, you’ll have to choose among several options, and some of the tools are less mature than others. Once you’re done, you can end up with a finely tuned collection of services that efficiently deliver what your users want. But it takes work and you’ll likely stub your toes a couple of times getting there.

All of the excitement and development around Kubernetes today means that future engineers will likely be able to build efficient, manageable services _without_ the toe stubbing.

## Serverless lets you focus on your application
“Serverless” architectures have been built around services like [Firebase](https://firebase.google.com), which allow developers to build client applications that connect to a server infrastructure the developer doesn’t need to manage. More recently, serverless has come to encompass “functions as a service,” most notably [Amazon’s Lambda](https://aws.amazon.com/lambda/). With Lambda, you’re still writing server-side code, but just in functions that take in data and send out a result, with the “server” part of it completely abstracted away. These functions are stateless and connect to services like [DynamoDB](https://aws.amazon.com/dynamodb/) or [Aurora](https://aws.amazon.com/rds/aurora/) for persistence.

A single function likely can’t act as a whole backend for an application. Building a serverless app therefore often includes creating multiple functions, setting up an [API Gateway](https://aws.amazon.com/api-gateway/), perhaps some queues and [Step Functions](https://aws.amazon.com/step-functions/) to glue things together, [X-Ray](https://aws.amazon.com/xray/) for debugging, etc.

All of those services are fully managed and scalable and don’t require the same attention to resource usage that Kubernetes does. Serverless frameworks (including [Serverless](https://serverless.com), [Up](https://github.com/apex/up), and [.architect](https://arc.codes)) help provide the glue and make local development easier.

Theoretically, if you build an application around functions, you can deploy a change in _seconds_, which is pretty cool. Functions-as-a-service (FaaS) takes the microservice idea as far as it can go (assuming no one’s about to introduce “line of code as a service”), making deployment units as small as can be, with the complexity coming in the form of coordination between those units.

In addition to the simple scaling offered by serverless, you also win by only paying for what you use. You don’t need to have frontend and database server instances running when nothing is happening on your site. A Kubernetes-based system could conceivably win on cost by building services that are finely tuned for your use cases. But that tuning takes effort and, without that effort, you’re more likely to be reserving more instances than a serverless implementation would.

Serverless frameworks today are young and largely tied to a single cloud provider, but over time I suspect we’ll see even easier ways to glue together autoscaling services from whichever providers give you the features you need.

## The serverless architecture used at Khan Academy
Why do people want serverless architectures? In my opinion, the reason to opt for a serverless architecture is because you want to focus on your application code and not focus on the infrastructure around building reliable, scalable services.

From the get-go, Khan Academy wanted a system that could scale as our usage increased, without requiring us to scale an operations team to match. Back when we started, the term “serverless” didn’t even exist and there were only a handful of services that would help you autoscale, notably Heroku and Google App Engine. We chose App Engine.

Today, Google compares App Engine to the new serverless frameworks, because it bundles [local development](https://cloud.google.com/appengine/downloads), data persistence (through [Datastore](https://cloud.google.com/appengine/docs/standard/#datastore)), monitoring and debugging (through [Stackdriver](https://cloud.google.com/stackdriver/)), and other features in simple, deployable units. You can even do [microservices with App Engine](https://cloud.google.com/appengine/docs/standard/python/microservices-on-app-engine).

App Engine has evolved over time, [adding Node to the supported languages on the Standard Environment](https://www.infoq.com/news/2018/05/gae-node), with the [Flexible Environment](https://cloud.google.com/appengine/docs/flexible/) going even further with support for custom Docker containers.

A framework like [.architect](https://arc.codes) pulls together the setup of a whole collection of AWS services to provide a cohesive experience. App Engine, too, was built to give developers an all-inclusive experience, and it provides that experience whether you’re deploying a single 100-line file or a much larger application.

I’m excited about all of the work going on around Kubernetes and function-based server architectures. The Kubernetes ecosystem is working out ways to provide tons of flexibility while improving manageability of services. The serverless crowd is working out new ways to spin up microservices where the hardware and networking is abstracted away. While these new technologies mature, our original serverless setup of App Engine continues to work well for us.

That said, whether you’re deploying to App Engine or EC2 today, I think it’s important to keep an eye on the fast-moving orchestration space.  We’re rapidly moving toward a world in which you can deploy applications constructed of just the services you need, with far greater cloud independence.

_Thanks to Ben Kraft, Craig Silverstein, Amos Latteier, and Marta Kosarchyn for their feedback on drafts of this article._

Discuss [on Hacker News](https://news.ycombinator.com/item?id=17197085)
