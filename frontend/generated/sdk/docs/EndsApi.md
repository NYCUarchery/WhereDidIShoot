# EndsApi

All URIs are relative to */api*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createEnd**](EndsApi.md#createend) | **POST** /ends | Create an end |
| [**deleteEnd**](EndsApi.md#deleteend) | **DELETE** /ends/{end_id} | Delete an end and all child records |
| [**getEnd**](EndsApi.md#getend) | **GET** /ends/{end_id} | Get an end |
| [**listEnds**](EndsApi.md#listends) | **GET** /ends | List ends |
| [**updateEnd**](EndsApi.md#updateend) | **PUT** /ends/{end_id} | Update an end |



## createEnd

> EndRecord createEnd(endInput)

Create an end

### Example

```ts
import {
  Configuration,
  EndsApi,
} from '';
import type { CreateEndRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new EndsApi();

  const body = {
    // EndInput
    endInput: ...,
  } satisfies CreateEndRequest;

  try {
    const data = await api.createEnd(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **endInput** | [EndInput](EndInput.md) |  | |

### Return type

[**EndRecord**](EndRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | End created successfully. |  -  |
| **400** | Request validation failed. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteEnd

> deleteEnd(endId)

Delete an end and all child records

### Example

```ts
import {
  Configuration,
  EndsApi,
} from '';
import type { DeleteEndRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new EndsApi();

  const body = {
    // number | Numeric end identifier
    endId: 56,
  } satisfies DeleteEndRequest;

  try {
    const data = await api.deleteEnd(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **endId** | `number` | Numeric end identifier | [Defaults to `undefined`] |

### Return type

`void` (Empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | End deleted successfully. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getEnd

> EndRecord getEnd(endId)

Get an end

### Example

```ts
import {
  Configuration,
  EndsApi,
} from '';
import type { GetEndRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new EndsApi();

  const body = {
    // number | Numeric end identifier
    endId: 56,
  } satisfies GetEndRequest;

  try {
    const data = await api.getEnd(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **endId** | `number` | Numeric end identifier | [Defaults to `undefined`] |

### Return type

[**EndRecord**](EndRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | End returned successfully. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## listEnds

> Array&lt;EndRecord&gt; listEnds(roundId)

List ends

### Example

```ts
import {
  Configuration,
  EndsApi,
} from '';
import type { ListEndsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new EndsApi();

  const body = {
    // number | Filter ends by their parent round (optional)
    roundId: 56,
  } satisfies ListEndsRequest;

  try {
    const data = await api.listEnds(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **roundId** | `number` | Filter ends by their parent round | [Optional] [Defaults to `undefined`] |

### Return type

[**Array&lt;EndRecord&gt;**](EndRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Ends returned successfully. |  -  |
| **400** | Request validation failed. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateEnd

> EndRecord updateEnd(endId, endInput)

Update an end

### Example

```ts
import {
  Configuration,
  EndsApi,
} from '';
import type { UpdateEndRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new EndsApi();

  const body = {
    // number | Numeric end identifier
    endId: 56,
    // EndInput
    endInput: ...,
  } satisfies UpdateEndRequest;

  try {
    const data = await api.updateEnd(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **endId** | `number` | Numeric end identifier | [Defaults to `undefined`] |
| **endInput** | [EndInput](EndInput.md) |  | |

### Return type

[**EndRecord**](EndRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | End updated successfully. |  -  |
| **400** | Request validation failed. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

