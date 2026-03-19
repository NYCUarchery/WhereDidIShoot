# RoundsApi

All URIs are relative to */api*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createRound**](RoundsApi.md#createround) | **POST** /rounds | Create a round |
| [**deleteRound**](RoundsApi.md#deleteround) | **DELETE** /rounds/{round_id} | Delete a round and all child records |
| [**getRound**](RoundsApi.md#getround) | **GET** /rounds/{round_id} | Get a round |
| [**listRounds**](RoundsApi.md#listrounds) | **GET** /rounds | List rounds |
| [**updateRound**](RoundsApi.md#updateround) | **PUT** /rounds/{round_id} | Update a round |



## createRound

> RoundRecord createRound(roundInput)

Create a round

### Example

```ts
import {
  Configuration,
  RoundsApi,
} from '';
import type { CreateRoundRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new RoundsApi();

  const body = {
    // RoundInput
    roundInput: ...,
  } satisfies CreateRoundRequest;

  try {
    const data = await api.createRound(body);
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
| **roundInput** | [RoundInput](RoundInput.md) |  | |

### Return type

[**RoundRecord**](RoundRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Round created successfully. |  -  |
| **400** | Request validation failed. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteRound

> deleteRound(roundId)

Delete a round and all child records

### Example

```ts
import {
  Configuration,
  RoundsApi,
} from '';
import type { DeleteRoundRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new RoundsApi();

  const body = {
    // number | Numeric round identifier
    roundId: 56,
  } satisfies DeleteRoundRequest;

  try {
    const data = await api.deleteRound(body);
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
| **roundId** | `number` | Numeric round identifier | [Defaults to `undefined`] |

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
| **204** | Round deleted successfully. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getRound

> RoundRecord getRound(roundId)

Get a round

### Example

```ts
import {
  Configuration,
  RoundsApi,
} from '';
import type { GetRoundRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new RoundsApi();

  const body = {
    // number | Numeric round identifier
    roundId: 56,
  } satisfies GetRoundRequest;

  try {
    const data = await api.getRound(body);
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
| **roundId** | `number` | Numeric round identifier | [Defaults to `undefined`] |

### Return type

[**RoundRecord**](RoundRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Round returned successfully. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## listRounds

> Array&lt;RoundRecord&gt; listRounds(practiceId)

List rounds

### Example

```ts
import {
  Configuration,
  RoundsApi,
} from '';
import type { ListRoundsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new RoundsApi();

  const body = {
    // number | Filter rounds by their parent practice (optional)
    practiceId: 56,
  } satisfies ListRoundsRequest;

  try {
    const data = await api.listRounds(body);
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
| **practiceId** | `number` | Filter rounds by their parent practice | [Optional] [Defaults to `undefined`] |

### Return type

[**Array&lt;RoundRecord&gt;**](RoundRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Rounds returned successfully. |  -  |
| **400** | Request validation failed. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateRound

> RoundRecord updateRound(roundId, roundInput)

Update a round

### Example

```ts
import {
  Configuration,
  RoundsApi,
} from '';
import type { UpdateRoundRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new RoundsApi();

  const body = {
    // number | Numeric round identifier
    roundId: 56,
    // RoundInput
    roundInput: ...,
  } satisfies UpdateRoundRequest;

  try {
    const data = await api.updateRound(body);
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
| **roundId** | `number` | Numeric round identifier | [Defaults to `undefined`] |
| **roundInput** | [RoundInput](RoundInput.md) |  | |

### Return type

[**RoundRecord**](RoundRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Round updated successfully. |  -  |
| **400** | Request validation failed. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

