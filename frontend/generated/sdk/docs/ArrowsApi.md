# ArrowsApi

All URIs are relative to */api*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createArrow**](ArrowsApi.md#createarrow) | **POST** /arrows | Create an arrow |
| [**deleteArrow**](ArrowsApi.md#deletearrow) | **DELETE** /arrows/{arrow_id} | Delete an arrow |
| [**getArrow**](ArrowsApi.md#getarrow) | **GET** /arrows/{arrow_id} | Get an arrow |
| [**listArrows**](ArrowsApi.md#listarrows) | **GET** /arrows | List arrows |
| [**updateArrow**](ArrowsApi.md#updatearrow) | **PUT** /arrows/{arrow_id} | Update an arrow |



## createArrow

> ArrowRecord createArrow(arrowInput)

Create an arrow

### Example

```ts
import {
  Configuration,
  ArrowsApi,
} from '';
import type { CreateArrowRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ArrowsApi();

  const body = {
    // ArrowInput
    arrowInput: ...,
  } satisfies CreateArrowRequest;

  try {
    const data = await api.createArrow(body);
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
| **arrowInput** | [ArrowInput](ArrowInput.md) |  | |

### Return type

[**ArrowRecord**](ArrowRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Arrow created successfully. |  -  |
| **400** | Request validation failed. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteArrow

> deleteArrow(arrowId)

Delete an arrow

### Example

```ts
import {
  Configuration,
  ArrowsApi,
} from '';
import type { DeleteArrowRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ArrowsApi();

  const body = {
    // number | Numeric arrow identifier
    arrowId: 56,
  } satisfies DeleteArrowRequest;

  try {
    const data = await api.deleteArrow(body);
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
| **arrowId** | `number` | Numeric arrow identifier | [Defaults to `undefined`] |

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
| **204** | Arrow deleted successfully. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getArrow

> ArrowRecord getArrow(arrowId)

Get an arrow

### Example

```ts
import {
  Configuration,
  ArrowsApi,
} from '';
import type { GetArrowRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ArrowsApi();

  const body = {
    // number | Numeric arrow identifier
    arrowId: 56,
  } satisfies GetArrowRequest;

  try {
    const data = await api.getArrow(body);
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
| **arrowId** | `number` | Numeric arrow identifier | [Defaults to `undefined`] |

### Return type

[**ArrowRecord**](ArrowRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Arrow returned successfully. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## listArrows

> Array&lt;ArrowRecord&gt; listArrows(endId)

List arrows

### Example

```ts
import {
  Configuration,
  ArrowsApi,
} from '';
import type { ListArrowsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ArrowsApi();

  const body = {
    // number | Filter arrows by their parent end (optional)
    endId: 56,
  } satisfies ListArrowsRequest;

  try {
    const data = await api.listArrows(body);
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
| **endId** | `number` | Filter arrows by their parent end | [Optional] [Defaults to `undefined`] |

### Return type

[**Array&lt;ArrowRecord&gt;**](ArrowRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Arrows returned successfully. |  -  |
| **400** | Request validation failed. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateArrow

> ArrowRecord updateArrow(arrowId, arrowInput)

Update an arrow

### Example

```ts
import {
  Configuration,
  ArrowsApi,
} from '';
import type { UpdateArrowRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ArrowsApi();

  const body = {
    // number | Numeric arrow identifier
    arrowId: 56,
    // ArrowInput
    arrowInput: ...,
  } satisfies UpdateArrowRequest;

  try {
    const data = await api.updateArrow(body);
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
| **arrowId** | `number` | Numeric arrow identifier | [Defaults to `undefined`] |
| **arrowInput** | [ArrowInput](ArrowInput.md) |  | |

### Return type

[**ArrowRecord**](ArrowRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Arrow updated successfully. |  -  |
| **400** | Request validation failed. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

