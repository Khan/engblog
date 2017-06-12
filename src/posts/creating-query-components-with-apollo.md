title: Creating Query Components with Apollo
published_on: June 12, 2017
author: Brian Genisio
team: Web Frontend
...

Here at Khan Academy, we've been using [GraphQL](http://graphql.org/) in several projects with great success.  GraphQL is a query language for describing the data you want from the backend API.  It is an elegant solution to some of the problems that REST presents, including client performance.

Prevailing wisdom in the React/GraphQL space these days suggests that queries be co-located with the components which use them.  We use [Apollo](http://dev.apollodata.com/) as our client abstraction to the GraphQL endpoint such that co-located queries are relatively straightforward to structure, at least for simple cases.  

As queries and component interactions become more complicated, however, the presentation and query layers become intertwined in a way that can feel overwhelming, especially from a [separation of concerns](https://en.wikipedia.org/wiki/Separation_of_concerns) perspective.  Because of this, we've started to adopt a pattern we are calling "Query Components".  I'll explain in more detail later in this post, but a Query Component is a component which abstracts the data definition from the [Presentational Component](https://medium.com/@dan_abramov/smart-and-dumb-components-7ca2f9a7c7d0), allowing the Presentational Component to be agnostic of Apollo or GraphQL.

## Demo code
All of the demo code for this post can be found in in this [Schools](https://github.com/BrianGenisio/schools) repo.  You can play with it [live](http://briangenisio.com/schools/) if you'd like.  There is not a ton of data, but it is an example of searching for schools by postal code.  Some postal codes with data include 48103, 48104, and 48105.  

It uses [GraphCool](https://www.graph.cool/) as the backend GraphQL implementation.  GraphCool is a really great way to experiment with GraphQL without learning how to implement a GraphQL server.  It is a Backend as a Service (BaaS) for implementing a data store with a GraphQL interface.

## A simple example
Let's start with a simple example of using Apollo to connect a GraphQL query to a React component.  Here is a Presentational Component which displays a list of all the schools available and a "Loading" string while we are waiting.  It is purposefully simple and shows how you can describe the data you want and display it with very little ceremony.

```jsx
import React, {Component} from 'react';
import {graphql} from 'react-apollo';
import gql from 'graphql-tag';

class Schools extends Component {
    render() {
        if (this.props.data.loading) {
            return <div>Loading</div>;
        }

        return <ul>
        {
            this.props.data.allSchools.map((school) =>
                <li key={school.id}>{school.display}</li>
        )}
        </ul>;
    }
}

const SCHOOLS_QUERY = gql`query allSchools {
  allSchools(orderBy: display_ASC) {
    id
    postalCode
    display
  }
}`;

export default graphql(SCHOOLS_QUERY)(Schools);
```

## A more complicated example
Unfortunately, simple examples like the one above are not the common case in practice.  Let's see how this expands to be more like what you'd see in a real application.

1. We'd like to pass a parameter to the component in order to filter the query by postal code.

1. In addition to the `data.loading` flag, we'd like to know when there was an error and we'd like to know when the query was successful but the result was empty.

1. We'd like to use [Flow](https://flow.org/) types, so we'll annotate all the types in this component.

1. We'd like to include [PropTypes](https://facebook.github.io/react/docs/typechecking-with-proptypes.html) in the component.  Since we are using Flow we'll do so via [Flow -> React PropTypes](https://www.npmjs.com/package/babel-plugin-flow-react-proptypes).

```jsx
// @flow

import React, {Component} from 'react';
import {graphql} from 'react-apollo';
import gql from 'graphql-tag';

type School = {
    id: string,
    postalCode: string,
    display: string,
}

class Schools extends Component {
    props: {
        // Provided by the parent component
        postalCode: string,

        // provided by the Apollo wrapper
        schools: Array<School>,
        isLoading: boolean,
        isEmpty: boolean,
        isError: boolean,
    }

    render() {
        const {schools, isLoading, isEmpty, isError} = this.props;

        if (isLoading) {
            return <div>Loading</div>;
        }

        if (isEmpty) {
            return <div>No items match your postal code</div>;
        }

        if (isError) {
            return <div>There was an error processing your search</div>;
        }

        return <ul>{
            schools.map((school) =>
                <li key={school.id}>{school.display}</li>
            )
        }</ul>;
    }
}

const SCHOOLS_QUERY = gql`query allSchools($postalCode: String!) {
  allSchools(
      orderBy: display_ASC,
      filter: {postalCode: $postalCode}
  ) {
    id
    postalCode
    display
  }
}`;

type SchoolsData =  {
    loading: boolean,
    error: string,
    allSchools?: Array<School>,
};

const mapDataToProps = ({data}: {data: SchoolsData}) => {
    const isLoading = data.loading;
    const isEmpty = !!data.allSchools && data.allSchools.length === 0;
    const isError = !!data.error;
    const schools = data.allSchools || [];

    return {isLoading, isEmpty, isError, schools};
};

const mapPropsToOptions = ({postalCode}) => ({variables: {postalCode}});

export default graphql(SCHOOLS_QUERY, {
    options: mapPropsToOptions,
    props: mapDataToProps,
})(Schools);
```

Now that we've added these features, we have a new set of problems.

1. The original code violates the "separation of concern" principle but this code is more egregious.  This component is managing the GraphQL/Apollo integration and the presentation at the same time.

1. The properties of the component don't properly communicate the intended usage.  The parent needs to provide the `postalCode` property, but the other required properties (`schools`, `isLoading`, `isEmpty`, and `isError`) are provided by the `mapDataToProps` function.

1. The actual presentation is tightly coupled to the query and glue logic.  It is not uncommon for the same query to be used for a select component, or a table layout, or some other presentation.  Providing a different presentation isn't immediately obvious.

## Query Components
A pattern we've liked using lately is something we are calling "Query Components".  Query Components encapsulate the query and Apollo glue logic into one component, which allows it to be composed with a separated Presentational Component.

It uses the ["Functions as Children"](https://facebook.github.io/react/docs/jsx-in-depth.html#functions-as-children) pattern.  For more information on this pattern, see Merrick Christensen's writeup in [Function as Child Components](https://medium.com/merrickchristensen/function-as-child-components-5f3920a9ace9).  

### SchoolsQuery
This is a Query Component which encapsulates all of the GraphQL query and the Apollo glue logic.  It doesn't have any presentation.

```jsx
// @flow
import gql from 'graphql-tag';
import {Component} from 'react';
import {graphql} from 'react-apollo';

export type School = {
    id: string,
    postalCode: string,
    display: string,
}

type SchoolQueryChildrenFn = (
    schools: Array<School>,
    details: {
        isLoading: boolean,
        isEmpty: boolean,
        isError: boolean,
    },
) => React$Element<any>;

class SchoolsQuery extends Component {
    props: {
        postalCode: string,
        children?: SchoolQueryChildrenFn,

        isLoading: boolean,
        isEmpty: boolean,
        isError: boolean,
        schools: Array<School>,
    }

    static defaultProps = {
        isLoading: false,
        isEmpty: false,
        isError: false,
        schools: [],
    }

    render() {
        const {isLoading, isEmpty, isError, schools, children} = this.props;

        return children && children(schools, {isLoading, isEmpty, isError});
    }
}

const SCHOOLS_QUERY = gql`query allSchools($postalCode: String!) {
  allSchools(
      orderBy: display_ASC,
      filter: {postalCode: $postalCode}
  ) {
    id
    postalCode
    display
  }
}`;

type SchoolsData =  {
    loading: boolean,
    error: string,
    allSchools?: Array<School>,
};

const mapDataToProps = ({data}: {data: SchoolsData}) => {
    const isLoading = data.loading;
    const isEmpty = !!data.allSchools && data.allSchools.length === 0;
    const isError = !!data.error;
    const schools = data.allSchools || [];

    return {isLoading, isEmpty, isError, schools};
};

const mapPropsToOptions = ({postalCode}) => ({variables: {postalCode}});

export default graphql(SCHOOLS_QUERY, {
    options: mapPropsToOptions,
    props: mapDataToProps,
})(SchoolsQuery);
```

### Schools component
This is a Presentational Component which composes itself with the Query Component and the presentation.  The interface is clear and the presentation is simple.

```jsx
// @flow

import React, {Component} from "react";

import SchoolsQuery from "./SchoolsQuery.js";

class Schools extends Component {
    props: {
        postalCode: string,
    }

    render() {
        const {postalCode} = this.props;

        return <SchoolsQuery postalCode={postalCode}>
            {(schools, {isLoading, isEmpty, isError}) => {
                if (isLoading) {
                    return <div>Loading</div>;
                }

                if (isEmpty) {
                    return <div>No items match your postal code</div>;
                }

                if (isError) {
                    return <div>There was an error processing your search</div>;
                }

                return <ul>{
                    schools.map((school) =>
                        <li key={school.id}>{school.display}</li>
                    )
                }</ul>;
            }}
        </SchoolsQuery>;
    }
}

export default Schools;
```

## Going forward
Query Components have been a valuable pattern within our codebase, but they are new to us, and we are still evaluating how the pattern will scale over time.  I expect an abstraction which codifies the pattern will be valuable.  I'd also like to see how the same concept can be used for other API interfaces.  The same approach would work for more traditional REST interfaces, for example.  Whatever the case, I expect that we will be blogging more about GraphQL in the future.

## Bonus!
This pattern can be applied to GraphQL mutations as well.  By separating the mutation into a Mutation Component, the presentation only needs to activate the mutation.  For the sake of brevity, I won't include the implementation here, but you can find it in the [demo code](https://github.com/BrianGenisio/schools/blob/master/src/NewSchoolMutation.js).

You can compose the Mutation Component with the presentation like this:

```jsx
<NewSchoolMutation
    postalCode={postalCode}
    display={display}
>
    {triggerMutation => <button onClick={triggerMutation}>
        Create!    
    </button>}
</NewSchoolMutation>
```
