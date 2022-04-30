#ifndef __QUAD_ENCODER_H
#define __QUAD_ENCODER_H

#ifdef __cplusplus
 extern "C" {
#endif 

#include "stm32f0xx_hal.h"
#include "helpers.h"

typedef struct
{
  GPIO_TypeDef* A_port;
  uint16_t A_pin;
  GPIO_TypeDef* B_port;
  uint16_t B_pin;
  uint8_t current_index;
} quad_output;

void quad_init(mouse_buf* mbuf, TIM_HandleTypeDef* avg_tim, TIM_HandleTypeDef* arr_tim, GPIO_TypeDef* x1_port, uint16_t x1_pin, GPIO_TypeDef* x2_port, uint16_t x2_pin);
void quad_increment(quad_output *qo);
void quad_decrement(quad_output *qo);
#ifdef __cplusplus
}
#endif

#endif


