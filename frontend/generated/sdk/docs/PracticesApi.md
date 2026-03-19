# PracticesApi

All URIs are relative to */api*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createPractice**](PracticesApi.md#createpractice) | **POST** /practices | Create a practice |
| [**deletePractice**](PracticesApi.md#deletepractice) | **DELETE** /practices/{practice_id} | Delete a practice and all child records |
| [**getPractice**](PracticesApi.md#getpractice) | **GET** /practices/{practice_id} | Get a practice |
| [**listPractices**](PracticesApi.md#listpractices) | **GET** /practices | List practices |
| [**updatePractice**](PracticesApi.md#updatepractice) | **PUT** /practices/{practice_id} | Update a practice |



## createPractice

> PracticeRecord createPractice(practiceInput)

Create a practice

### Example

```ts
import {
  Configuration,
  PracticesApi,
} from '';
import type { CreatePracticeRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new PracticesApi();

  const body = {
    // PracticeInput
    practiceInput: ...,
  } satisfies CreatePracticeRequest;

  try {
    const data = await api.createPractice(body);
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
| **practiceInput** | [PracticeInput](PracticeInput.md) |  | |

### Return type

[**PracticeRecord**](PracticeRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Practice created successfully. |  -  |
| **400** | Request validation failed. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deletePractice

> deletePractice(practiceId)

Delete a practice and all child records

### Example

```ts
import {
  Configuration,
  PracticesApi,
} from '';
import type { DeletePracticeRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new PracticesApi();

  const body = {
    // number | Numeric practice identifier
    practiceId: 56,
  } satisfies DeletePracticeRequest;

  try {
    const data = await api.deletePractice(body);
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
| **practiceId** | `number` | Numeric practice identifier | [Defaults to `undefined`] |

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
| **204** | Practice deleted successfully. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getPractice

> PracticeRecord getPractice(practiceId)

Get a practice

### Example

```ts
import {
  Configuration,
  PracticesApi,
} from '';
import type { GetPracticeRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new PracticesApi();

  const body = {
    // number | Numeric practice identifier
    practiceId: 56,
  } satisfies GetPracticeRequest;

  try {
    const data = await api.getPractice(body);
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
| **practiceId** | `number` | Numeric practice identifier | [Defaults to `undefined`] |

### Return type

[**PracticeRecord**](PracticeRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Practice returned successfully. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## listPractices

> Array&lt;PracticeRecord&gt; listPractices(userId)

List practices

### Example

```ts
import {
  Configuration,
  PracticesApi,
} from '';
import type { ListPracticesRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new PracticesApi();

  const body = {
    // number | Filter practices by their parent user (optional)
    userId: 56,
  } satisfies ListPracticesRequest;

  try {
    const data = await api.listPractices(body);
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
| **userId** | `number` | Filter practices by their parent user | [Optional] [Defaults to `undefined`] |

### Return type

[**Array&lt;PracticeRecord&gt;**](PracticeRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Practices returned successfully. |  -  |
| **400** | Request validation failed. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updatePractice

> PracticeRecord updatePractice(practiceId, practiceInput)

Update a practice

### Example

```ts
import {
  Configuration,
  PracticesApi,
} from '';
import type { UpdatePracticeRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new PracticesApi();

  const body = {
    // number | Numeric practice identifier
    practiceId: 56,
    // PracticeInput
    practiceInput: ...,
  } satisfies UpdatePracticeRequest;

  try {
    const data = await api.updatePractice(body);
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
| **practiceId** | `number` | Numeric practice identifier | [Defaults to `undefined`] |
| **practiceInput** | [PracticeInput](PracticeInput.md) |  | |

### Return type

[**PracticeRecord**](PracticeRecord.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Practice updated successfully. |  -  |
| **400** | Request validation failed. |  -  |
| **404** | The requested record was not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

