<?php

use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Route;

$health = static fn (): JsonResponse => response()->json([
    'service' => 'research-os-laravel-platform',
    'status' => 'ok',
    'contract_version' => '1.0.0',
]);

$ready = static fn (): JsonResponse => response()->json([
    'service' => 'research-os-laravel-platform',
    'status' => 'ready',
    'contract_version' => '1.0.0',
]);

Route::get('/health', $health);
Route::get('/ready', $ready);

Route::prefix('v1')->group(function () use ($health, $ready): void {
    Route::get('/health', $health);
    Route::get('/ready', $ready);
});
