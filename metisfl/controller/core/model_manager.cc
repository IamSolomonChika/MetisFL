#include "metisfl/controller/core/model_manager.h"

namespace metisfl::controller {

// Constructor
ModelManager::ModelManager(const GlobalTrainParams &global_train_params,
                           const ModelStoreParams &model_store_params)
    : model_store_mutex_(),
      model_(),
      global_train_params_(global_train_params) {
  model_store_ = CreateModelStore(model_store_params);
  aggregator_ = CreateAggregator(global_train_params);
}

// Public methods

absl::Status ModelManager::SetInitialModel(const Model &model) {
  if (is_initialized_)
    return absl::FailedPreconditionError("Model is already initialized.");

  PLOG(INFO) << "Received initial model.";
  model_ = model;
  is_initialized_ = true;
  return absl::OkStatus();
}

void ModelManager::InsertModel(std::string learner_id, const Model &model) {
  std::lock_guard<std::mutex> model_store_guard(model_store_mutex_);

  model_store_->InsertModel(std::vector<std::pair<std::string, Model>>{
      std::pair<std::string, Model>(learner_id, model)});
}

void ModelManager::EraseModels(std::vector<std::string> learner_id) {
  std::lock_guard<std::mutex> model_store_guard(model_store_mutex_);
  model_store_->EraseModels(learner_id);
}

void ModelManager::UpdateModel(
    std::vector<std::string> learner_ids,
    absl::flat_hash_map<std::string, double> scaling_factors) {
  std::lock_guard<std::mutex> model_store_guard(model_store_mutex_);

  auto update_id = InitializeMetadata();
  int stride_length = GetStrideLength(learner_ids.size());

  std::chrono::time_point<std::chrono::system_clock> start_time_aggregation =
      std::chrono::high_resolution_clock::now();

  for (std::string learner_id : learner_ids) {
    auto lineage_length = GetLineageLength(learner_id);
    std::vector<std::pair<std::string, int>> to_select_block;

    to_select_block.emplace_back(learner_id, lineage_length);
    int block_size = to_select_block.size();

    if (block_size == stride_length || learner_id == learner_ids.back()) {
      auto selected_models = SelectModels(update_id, to_select_block);

      auto to_aggregate_block =
          GetAggregationPairs(selected_models, scaling_factors);

      Aggregate(update_id, to_aggregate_block);

      RecordBlockSize(update_id, block_size);

      model_store_->ResetState();
    }
  }

  RecordAggregationTime(update_id, start_time_aggregation);
  RecordModelSize(update_id);
  aggregator_->Reset();
}

void ModelManager::Shutdown() { model_store_->Shutdown(); }

std::string ModelManager::InitializeMetadata() {
  auto update_id = metisfl::controller::GenerateRadnomId();
  metadata_[update_id] = ModelMetadata();
  return update_id;
}

// Private methods
int ModelManager::GetStrideLength(int num_learners) const {
  uint32_t stride_length = num_learners;
  if (global_train_params_.aggregation_rule == "FedStride") {
    auto fed_stride_length = global_train_params_.stride_length;
    if (fed_stride_length > 0) {
      stride_length = fed_stride_length;
    }
  }
  return stride_length;
}

int ModelManager::GetLineageLength(std::string learner_id) const {
  const auto lineage_length = model_store_->GetLearnerLineageLength(learner_id);

  auto required_lineage_length = aggregator_->RequiredLearnerLineageLength();

  return std::min(lineage_length, required_lineage_length);
}

std::map<std::string, std::vector<const Model *>> ModelManager::SelectModels(
    std::string update_id,
    std::vector<std::pair<std::string, int>> to_select_block) {
  auto start_time_selection = std::chrono::high_resolution_clock::now();

  std::map<std::string, std::vector<const Model *>> selected_models =
      model_store_->SelectModels(to_select_block);

  auto end_time_selection = std::chrono::high_resolution_clock::now();

  std::chrono::duration<double, std::milli> elapsed_time_selection =
      end_time_selection - start_time_selection;

  metadata_[update_id].set_selection_duration_ms(
      elapsed_time_selection.count());

  return selected_models;
}

std::vector<std::vector<std::pair<const Model *, double>>>
ModelManager::GetAggregationPairs(
    std::map<std::string, std::vector<const Model *>> selected_models,
    absl::flat_hash_map<std::string, double> scaling_factors) const {
  std::vector<std::vector<std::pair<const Model *, double>>> to_aggregate_block;

  std::vector<std::pair<const Model *, double>> to_aggregate_learner_models_tmp;

  for (auto const &[selected_learner_id, selected_learner_models] :
       selected_models) {
    auto scaling_factor = scaling_factors[selected_learner_id];

    for (auto it : selected_learner_models) {
      to_aggregate_learner_models_tmp.emplace_back(it, scaling_factor);
    }

    to_aggregate_block.push_back(to_aggregate_learner_models_tmp);
    to_aggregate_learner_models_tmp.clear();
  }

  return to_aggregate_block;
}

void ModelManager::Aggregate(
    std::string update_id,
    std::vector<std::vector<std::pair<const Model *, double>>>
        to_aggregate_block) {
  auto start_time_block_aggregation = std::chrono::high_resolution_clock::now();

  model_ = aggregator_->Aggregate(to_aggregate_block);

  auto end_time_block_aggregation = std::chrono::high_resolution_clock::now();

  std::chrono::duration<double, std::milli> elapsed_time_block_aggregation =
      end_time_block_aggregation - start_time_block_aggregation;

  *metadata_[update_id].mutable_aggregation_block_duration_ms()->Add() =
      elapsed_time_block_aggregation.count();
}

void ModelManager::RecordBlockSize(std::string update_id, int block_size) {
  *metadata_[update_id].mutable_aggregation_block_size()->Add() = block_size;
  long block_memory = GetTotalMemory();
  *metadata_[update_id].mutable_aggregation_block_memory_kb()->Add() =
      (double)block_memory;
}

void ModelManager::RecordAggregationTime(
    std::string update_id,
    std::chrono::time_point<std::chrono::system_clock> start) {
  auto end = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double, std::milli> elapsed = end - start;
  metadata_[update_id].set_aggregation_duration_ms(elapsed.count());
}

void ModelManager::RecordModelSize(std::string &update_id) {
  // TODO:
}

};  // namespace metisfl::controller
